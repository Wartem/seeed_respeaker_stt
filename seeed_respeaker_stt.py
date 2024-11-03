# Seeed ReSpeaker Speech-to-Text
# Tested on:
#   Updated Raspberry Pi 5,
#   Linux kernel: 6.6.51+rpt-rpi-2712,
#   ReSpeaker 2-Mics Pi HAT

#!/usr/bin/env python3

from audio_handler import AudioHandler
import signal
import sys

import signal
import sys
import atexit
import os
import psutil
from audio_handler import AudioHandler
import logging

""" ReSpeaker 2-Mics Pi HAT setup
Device: hw:0,0 (which corresponds to device index 0)
Format: S16_LE (which is 16-bit signed little-endian). Equivalent to `pyaudio.paInt16`.
Sample rate: 48000
Channels: 2 (for the second command)
"""

from audio_handler import AudioHandler

"""
This script is designed to handle audio recording and speech recognition using the Vosk library.

It sets up an audio handler that records audio from the default input device, performs voice activity detection, 
and processes the audio using the Vosk speech recognition library.

The script can be run as a standalone program, and it will continuously record and recognize speech until it is stopped.

Usage:
    python audio_handler.py

Note:
    This script requires the Vosk library and its dependencies to be installed.
    It also requires a working audio input device.
"""

class GracefulKiller:
    """Handles graceful shutdown of the application."""

    def __init__(self, logger):
        self.kill_now = False
        self.logger = logger
        self.shutdown_handlers = []

        # Register signal handlers
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        # Register cleanup on normal exit
        atexit.register(self._cleanup)

    def _exit_gracefully(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"\nReceived signal {signum}, shutting down...")
        self.kill_now = True
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """Run all registered cleanup handlers."""
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                self.logger.error(f"Error in cleanup handler: {e}")

    def add_shutdown_handler(self, handler):
        """Add a function to be called during cleanup."""
        self.shutdown_handlers.append(handler)

def force_kill_audio_processes():
    """Force kill any hanging audio processes."""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)

    # Kill child processes
    children = current_process.children(recursive=True)
    for child in children:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass

def reset_audio_device():
    """Reset the audio device."""
    try:
        os.system("sudo alsa force-reload >/dev/null 2>&1")
    except Exception:
        pass

if __name__ == "__main__":
    # Setup logging
    logger = logging.getLogger("MainScript")
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Initialize graceful killer
    killer = GracefulKiller(logger)
    audio_handler = None

    try:
        # Create audio handler
        audio_handler = AudioHandler()

        # Register cleanup handlers
        killer.add_shutdown_handler(
            lambda: audio_handler.cleanup() if audio_handler else None
        )
        killer.add_shutdown_handler(force_kill_audio_processes)
        killer.add_shutdown_handler(reset_audio_device)

        # Start recording
        audio_handler.start_recording()
        logger.info("Recording... Press Ctrl+C to stop")
        logger.info("Speak clearly into the microphone...")

        # Main loop
        while not killer.kill_now:
            try:
                result = audio_handler.process_audio()
                if result:
                    if result.startswith("(Partial)"):
                        print(f"\r{result}", end="", flush=True)
                    else:
                        print(f"\nRecognized: {result}")
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                break

    except KeyboardInterrupt:
        logger.info("\nStopping...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Final cleanup
        try:
            logger.info("Shutting down...")

            if audio_handler:
                audio_handler.cleanup()

            logger.info("Forcing cleanup of audio processes...")
            force_kill_audio_processes()

            logger.info("Resetting audio device...")
            reset_audio_device()

            # Reset audio system
            logger.info("Resetting audio system...")
            os.system("./reset_audio.sh")

        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")

        logger.info("Program terminated")
        sys.exit(0)
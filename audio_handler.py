from collections import deque
import logging
import queue
from typing import Optional
import os

import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer

from logger_config import LoggerConfig
from config_manager import ConfigManager
from audio.audio_config import AudioConfig
from audio.audio_device_manager import AudioDeviceManager
from audio.audio_processor import AudioProcessor
from audio.audio_stream_handler import AudioStreamHandler
from setup_vosk_model import setup_vosk_model

class AudioHandler:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize AudioHandler with configuration."""
        # Initialize logger first
        self.debug_mode = False
        self.logger = LoggerConfig.setup_logger(self.debug_mode)
        
        # Initialize ConfigManager
        self.config_manager = ConfigManager(config_path, logger=self.logger)
        
        # Update debug mode from config
        self.debug_mode = self.config_manager.config.get("DEBUG_MODE", False)
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # Initialize components
        self.config = AudioConfig()
        self._update_config_from_manager()
        
        self.audio = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.stream = None
        
        # Initialize helper components
        self.device_manager = AudioDeviceManager(self.config, self.logger)
        self.device_manager.audio = self.audio  # Share PyAudio instance
        
        self.audio_processor = AudioProcessor(self.config, self.logger)
        self.stream_handler = AudioStreamHandler(self.config, self.audio_queue, self.logger)
        
        try:
            # Setup devices using device manager
            self.device_manager.setup_devices()
            
            # Initialize Vosk
            self._initialize_vosk()
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {str(e)}")
            self.cleanup()
            raise

    def _update_config_from_manager(self):
        """Update AudioConfig with values from ConfigManager."""
        audio_config = self.config_manager.get_audio_config()
        
        # Update basic audio settings
        self.config.RATE = audio_config["RATE"]
        self.config.CHANNELS = audio_config["CHANNELS"]
        self.config.CHUNK = audio_config["CHUNK"]
        self.config.VAD_THRESHOLD = audio_config["VAD_THRESHOLD"]
        
        # Keep format hardcoded for ReSpeaker compatibility
        self.config.FORMAT = pyaudio.paInt16
        
        self.logger.info("Audio configuration updated from config manager")

    def _initialize_vosk(self):
        """Initialize Vosk speech recognition."""
        try:
            model_path = setup_vosk_model(self.config_manager.get_model_path())
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.config.RATE)
            self.recognizer.SetWords(True)
            self.logger.info("Vosk model initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing speech recognition: {str(e)}")
            raise

    def start_recording(self):
        """Start recording with proper error handling."""
        try:
            self.stream = self.audio.open(
                format=self.config.FORMAT,
                channels=self.config.CHANNELS,
                rate=self.config.RATE,
                input=True,
                input_device_index=self.config.DEVICE_INDEX,
                frames_per_buffer=self.config.CHUNK,
                stream_callback=self.stream_handler.audio_callback,
                start=False
            )
            
            self.stream.start_stream()
            self.is_running = True
            self.logger.info("Started recording successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {str(e)}")
            self.cleanup()
            raise

    def process_audio(self) -> Optional[str]:
        """Process audio and return recognized text."""
        try:
            audio_data = self.audio_queue.get_nowait()
            
            # Skip processing if audio is too quiet
            if np.max(np.abs(audio_data)) < (self.config.VAD_THRESHOLD * 32768):
                return None
            
            # Process audio using the processor
            if self.recognizer.AcceptWaveform(audio_data.tobytes()):
                return self.audio_processor.process_recognition_result(self.recognizer)
            else:
                return self.audio_processor.process_partial_result(self.recognizer)
                
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
        return None

    def cleanup(self):
        """Enhanced cleanup with better error handling."""
        cleanup_successful = True
        
        try:
            # Stop recording
            self.is_running = False
            
            # Clear the audio queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Clean up the audio stream
            if self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                except Exception as e:
                    self.logger.error(f"Error closing stream: {e}")
                    cleanup_successful = False
            
            # Clean up PyAudio
            if self.audio:
                try:
                    self.audio.terminate()
                    self.audio = None
                except Exception as e:
                    self.logger.error(f"Error terminating PyAudio: {e}")
                    cleanup_successful = False
            
            # Clean up Vosk resources
            if hasattr(self, 'recognizer'):
                self.recognizer = None
            if hasattr(self, 'model'):
                self.model = None
            
            # Final status message
            if cleanup_successful:
                self.logger.info("Cleanup completed successfully")
            else:
                self.logger.warning("Cleanup completed with some errors")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            cleanup_successful = False
            
        return cleanup_successful

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
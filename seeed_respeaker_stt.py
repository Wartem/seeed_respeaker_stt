# Seeed ReSpeaker Speech-to-Text 
# Tested on:
#   Updated Raspberry Pi 5, 
#   Linux kernel: 6.6.51+rpt-rpi-2712,
#   ReSpeaker 2-Mics Pi HAT

""" ReSpeaker 2-Mics Pi HAT setup
Device: hw:0,0 (which corresponds to device index 0)
Format: S16_LE (which is 16-bit signed little-endian). Equivalent to `pyaudio.paInt16`.
Sample rate: 48000
Channels: 2 (for the second command)
"""

import pyaudio
import numpy as np
import queue
import logging
from typing import Dict, Optional
from vosk import Model, KaldiRecognizer
import json
import wget
import zipfile
import shutil
from pathlib import Path
import psutil
import time
from datetime import datetime

class LoggerConfig:
    """Centralized logging configuration"""
    
    @staticmethod
    def setup_logger(debug_mode: bool = False) -> logging.Logger:
        """
        Configure and return a logger instance with appropriate level and formatting
        
        Args:
            debug_mode: Whether to set logging level to DEBUG
            
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger('AudioHandler')
        if not logger.handlers:  # Prevent duplicate handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        return logger

class AudioDiagnostics:
    def __init__(self, debug_mode: bool = False, logger: Optional[logging.Logger] = None):
        self.start_time = time.time()
        self.last_check = self.start_time
        self.samples_processed = 0
        self.cpu_usage = []
        self.debug_mode = debug_mode
        self.logger = logger or LoggerConfig.setup_logger(debug_mode)
        
    def update(self, sample_size: int) -> None:
        """
        Update diagnostics with new sample data
        
        Args:
            sample_size: Number of samples processed
        """
        current_time = time.time()
        self.samples_processed += sample_size
        
        if self.debug_mode and current_time - self.last_check >= 1.0:
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_usage.append(cpu_percent)
            
            self.logger.debug(
                f"\nDiagnostics at {datetime.now().strftime('%H:%M:%S')}:\n"
                f"- CPU Usage: {cpu_percent}%\n"
                f"- Samples processed: {self.samples_processed}\n"
                f"- Time running: {int(current_time - self.start_time)}s\n"
                f"- Sample rate actual: {self.samples_processed / (current_time - self.start_time):.2f} Hz"
            )
            self.last_check = current_time
class ConfigManager:
    
    DEFAULT_CONFIG_PATH = "config.json"
    
    DEFAULT_CONFIG = {
        "MODEL_PATH": "path_to_default_model",
        "SAMPLE_RATE": 48000,
        "CHANNELS": 2,
        "CHUNK_SIZE": 8000,
        "VAD_THRESHOLD": 0.001,
        "DEBUG_MODE": False,
    }
    
    def __init__(self, config_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or LoggerConfig.setup_logger()
        self.config_path = Path(config_path if config_path else self.DEFAULT_CONFIG_PATH)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """
        Load configuration with enhanced error handling and logging
        """
        try:
            if not self.config_path.exists():
                self.logger.warning(
                    f"Configuration file not found at {self.config_path}, creating default"
                )
                self._create_default_config()
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Validate and merge with defaults
            merged_config = self.DEFAULT_CONFIG.copy()
            merged_config.update(config)
            
            self.logger.info("Configuration loaded successfully")
            return merged_config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {str(e)}")
            return self.DEFAULT_CONFIG.copy()
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing configuration file: {str(e)}")
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {str(e)}")
            return self.DEFAULT_CONFIG.copy()
        
    def _create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        self.logger.info(f"Creating default configuration file at {self.config_path}")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=4)
    
    def get_model_path(self) -> str:
        """Get the model path from configuration."""
        return self.config["MODEL_PATH"]
    
    def get_audio_config(self) -> Dict:
        """Get audio-related configuration."""
        return {
            "RATE": self.config["SAMPLE_RATE"],
            "CHANNELS": self.config["CHANNELS"],
            "CHUNK": self.config["CHUNK_SIZE"],
            "VAD_THRESHOLD": self.config["VAD_THRESHOLD"]
        }

def setup_vosk_model(model_path: str) -> Optional[str]:
    """
    Ensures the Vosk model exists at the specified path, downloading it if necessary.
    
    Args:
        model_path: Path to the model directory
        
    Returns:
        str: Path to the model directory if successful, None if failed
    """
    model_path = Path(model_path)
    zip_path = None
    logger = logging.getLogger(__name__)
    
    if model_path.exists():
        logger.info(f"Model already exists at {model_path}")
        return str(model_path)
        
    try:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_name = model_path.name
        
        base_url = "https://alphacephei.com/vosk/models"
        zip_filename = f"{model_name}.zip"
        download_url = f"{base_url}/{zip_filename}"
        
        logger.info(f"Downloading Vosk model from {download_url}")
        zip_path = model_path.parent / zip_filename
        wget.download(download_url, str(zip_path))
        logger.info("Download completed")
        
        logger.info(f"Extracting model to {model_path.parent}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(str(model_path.parent))
            
        logger.info(f"Removing temporary zip file: {zip_path}")
        if zip_path.exists():
            zip_path.unlink()
            logger.info("Zip file removed successfully")
        
        logger.info("Model setup completed successfully")
        return str(model_path)
        
    except Exception as e:
        logger.error(f"Error setting up Vosk model: {str(e)}")
        if zip_path and zip_path.exists():
            logger.info(f"Cleaning up temporary zip file: {zip_path}")
            zip_path.unlink()
        if model_path.exists():
            logger.info(f"Cleaning up partial model directory: {model_path}")
            shutil.rmtree(model_path)
        raise

class AudioConfig:
    """
    Audio configuration for Seeed 2-mic.

    Attributes:
        RATE (int): The sample rate of the audio. Vosk expects a rate of 16000, but this is set to 48000.
        CHANNELS (int): The number of channels for the audio input. Seeed 2-mic requires 2 channels.
        CHUNK (int): The size of each chunk of audio data.
        FORMAT (int): The format of the audio data. This is set to pyaudio.paInt16, which is 16-bit signed little-endian.
        DEVICE_INDEX (Optional[int]): The index of the device to use for audio input. This is set to None.
        VAD_THRESHOLD (float): The threshold for voice activity detection.
    """
    RATE=48000
    CHANNELS = 2  # Seeed 2-mic requires 2 channels for input
    CHUNK = 8000
    FORMAT = pyaudio.paInt16
    DEVICE_INDEX = None
    VAD_THRESHOLD = 0.001

class AudioHandler:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AudioHandler with configuration.
        
        Args:
            config_path: Optional path to config file
        """
        # Initialize logger first
        self.debug_mode = False  # Will be updated from config
        self.logger = LoggerConfig.setup_logger(self.debug_mode)
        
        # Load configuration
        self.config_manager = ConfigManager(config_path, logger=self.logger)
        audio_config = self.config_manager.get_audio_config()
        
        # Update debug mode from config
        self.debug_mode = self.config_manager.config.get("DEBUG_MODE", False)
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # Initialize diagnostics with logger
        self.diagnostics = AudioDiagnostics(
            debug_mode=self.debug_mode,
            logger=self.logger
        )
        
        # Initialize audio configuration
        self.config = AudioConfig()
        self.config.RATE = audio_config["RATE"]
        self.config.CHANNELS = audio_config["CHANNELS"]
        self.config.CHUNK = audio_config["CHUNK"]
        self.config.VAD_THRESHOLD = audio_config["VAD_THRESHOLD"]
        
        self.audio = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        try:
            # Initialize audio device
            self._setup_devices()
            
            # Initialize Vosk
            self._initialize_vosk()
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {str(e)}")
            self.cleanup()
            raise

    def _initialize_vosk(self):
        """Initialize Vosk speech recognition with model download"""
        try:
            model_path = setup_vosk_model(self.config_manager.get_model_path())
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.config.RATE)
            self.recognizer.SetWords(True)
            self.partial_result = ""
            self.logger.info("Vosk model initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing speech recognition: {str(e)}")
            raise

    def _setup_devices(self):
        """Find and setup Seeed 2-mic device with proper configuration"""
        try:
            # Log available devices
            self._log_available_devices()
            
            # Look for Seeed device
            seeed_device = self._find_seeed_device()
            
            if seeed_device is not None:
                self.config.DEVICE_INDEX = seeed_device['index']
                self.config.CHANNELS = min(seeed_device['maxInputChannels'], 2)
                self.logger.info(f"Selected Seeed 2-mic at index {self.config.DEVICE_INDEX}")
                self.logger.info(f"Using {self.config.CHANNELS} channels")
            else:
                self._setup_default_device()
                
        except Exception as e:
            self.logger.error(f"Error setting up audio devices: {str(e)}")
            raise

    def _log_available_devices(self):
        """Log information about all available audio devices"""
        self.logger.info("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if self.debug_mode:
                self.logger.debug(
                    f"Device {i}: {dev_info['name']}\n"
                    f"  Max Input Channels: {dev_info['maxInputChannels']}\n"
                    f"  Default Sample Rate: {dev_info['defaultSampleRate']}\n"
                    f"  Default Low Input Latency: {dev_info['defaultLowInputLatency']}\n"
                    f"  Default High Input Latency: {dev_info['defaultHighInputLatency']}"
                )
            
            # Update rate if needed
            if dev_info['defaultSampleRate'] != self.config.RATE:
                self.logger.warning(
                    f"Device {i} default sample rate {dev_info['defaultSampleRate']} "
                    f"does not match configured rate {self.config.RATE}"
                )
                self.config.RATE = int(dev_info['defaultSampleRate'])

    def _find_seeed_device(self):
        """Find Seeed 2-mic device if available"""
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if "seeed" in dev_info['name'].lower():
                if self.debug_mode:
                    self.logger.debug(f"Found Seeed device: {dev_info}")
                return dev_info
        return None

    def _setup_default_device(self):
        """Setup default audio device when Seeed device is not found"""
        self.logger.warning("Seeed 2-mic not found, using default device")
        default_input = self.audio.get_default_input_device_info()
        self.config.DEVICE_INDEX = default_input['index']
        self.config.CHANNELS = min(default_input['maxInputChannels'], 2)
        self.logger.info(f"Using default input device: {default_input['name']}")
        self.logger.info(f"Using {self.config.CHANNELS} channels")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Handle incoming audio data with improved error handling and logging"""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        
        try:
            # Convert to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            if self.debug_mode:
                audio_level = np.abs(audio_data).mean()
                if audio_level > 500:
                    self.logger.debug(f"Audio level: {audio_level}")
            
            # Process audio data
            audio_data = audio_data.reshape(-1, 2)
            mono_data = audio_data.mean(axis=1).astype(np.int16)
            normalized = mono_data.astype(np.float32) / 32768.0
            
            # Voice Activity Detection
            voice_level = np.abs(normalized).mean()
            if self.debug_mode and voice_level > self.config.VAD_THRESHOLD:
                self.logger.debug(f"Voice detected! Level: {voice_level:.4f}")
            
            if voice_level > self.config.VAD_THRESHOLD:
                self.audio_queue.put(mono_data.copy())
            
            # Update diagnostics
            self.diagnostics.update(len(mono_data))
            
            return (None, pyaudio.paContinue)
            
        except Exception as e:
            self.logger.error(f"Error in audio callback: {str(e)}")
            return (None, pyaudio.paComplete)

    def start_recording(self):
        """Start audio recording with improved error handling"""
        try:
            self.is_running = True
            
            self.stream = self.audio.open(
                format=self.config.FORMAT,
                channels=self.config.CHANNELS,
                rate=self.config.RATE,
                input=True,
                output=False,
                input_device_index=self.config.DEVICE_INDEX,
                frames_per_buffer=self.config.CHUNK,
                stream_callback=self._audio_callback,
                start=False
            )
            
            self.stream.start_stream()
            self.logger.info("Started recording successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {str(e)}")
            self.cleanup()
            raise

    def process_audio(self) -> Optional[str]:
        """Process audio from queue and return recognized text"""
        try:
            audio_data = self.audio_queue.get_nowait()
            if self.recognizer.AcceptWaveform(audio_data.tobytes()):
                result = json.loads(self.recognizer.Result())
                if result.get("text"):
                    return result["text"]
            else:
                partial = json.loads(self.recognizer.PartialResult())
                if partial.get("partial"):
                    self.partial_result = partial["partial"]
                    return f"(Partial) {self.partial_result}"
                    
        except queue.Empty:
            pass
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding recognition result: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
        return None

    def cleanup(self):
        """Cleanup resources with improved error handling"""
        self.is_running = False
        
        if hasattr(self, 'stream'):
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                self.logger.error(f"Error closing stream: {str(e)}")
        
        try:
            self.audio.terminate()
        except Exception as e:
            self.logger.error(f"Error terminating PyAudio: {str(e)}")
            
        self.logger.info("Audio resources cleaned up")

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

if __name__ == "__main__":
    audio_handler = AudioHandler()
    try:
        audio_handler.start_recording()
        print("Recording... Press Ctrl+C to stop")
        print("Speak clearly into the microphone...")
        
        while True:
            result = audio_handler.process_audio()
            if result:
                if result.startswith("(Partial)"):
                    print(f"\r{result}", end="", flush=True)
                else:
                    print(f"\nRecognized: {result}")
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        audio_handler.cleanup()
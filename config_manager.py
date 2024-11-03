
# config_manager.py

import logging
from typing import Dict, Optional
import json
from pathlib import Path
from logger_config import LoggerConfig

class ConfigManager:
    
    DEFAULT_CONFIG_PATH = "config.json"
    
    DEFAULT_CONFIG = {
        "MODEL_PATH": "./vosk-models/vosk-model-small-en-us-zamia-0.5",
        "SAMPLE_RATE": 48000,
        "CHANNELS": 2,
        "CHUNK_SIZE": 2000,  # Reduced chunk size for better responsiveness. Try 8000.
        "VAD_THRESHOLD": 0.01,
        "SILENCE_THRESHOLD": 0.008,
        "MIN_PHRASE_MS": 500,
        "MAX_PHRASE_MS": 10000,
        "SILENCE_MS": 300,
        "DEBUG_MODE": False
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
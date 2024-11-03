# logger_config.py
import logging

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
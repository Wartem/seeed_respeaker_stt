# audio_diagnostics.py

import logging
from typing import Optional
import psutil
import time
from datetime import datetime
from config_manager import LoggerConfig

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
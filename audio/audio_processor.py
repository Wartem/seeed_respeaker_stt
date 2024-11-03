import numpy as np
from typing import Optional
import json

class AudioProcessor:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._last_partial = None

    def resample_audio(self, audio_data):
        """Resample audio from 48kHz to 16kHz with improved quality"""
        try:
            # Ensure audio_data is the right shape
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
                
            resampling_factor = self.config.VOSK_RATE / self.config.RATE
            resampled_len = int(len(audio_data) * resampling_factor)
            
            # Use scipy.signal.resample for better quality
            from scipy import signal
            resampled_data = signal.resample(audio_data, resampled_len)
            
            # Ensure output is in the correct range
            resampled_data = np.clip(resampled_data, -32768, 32767)
            return resampled_data.astype(np.int16)
            
        except Exception as e:
            self.logger.error(f"Resampling error: {str(e)}")
            return audio_data  # Return original data if resampling fails

    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Enhanced audio preprocessing."""
        try:
            # Convert to float32 for processing
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Noise reduction
            noise_floor = np.mean(np.abs(audio_float[audio_float < self.config.VAD_THRESHOLD]))
            audio_float = np.where(
                np.abs(audio_float) < noise_floor * 2,
                0,
                audio_float
            )
            
            # Optional: Add high-pass filter if scipy is available
            try:
                from scipy import signal
                b, a = signal.butter(4, 80.0/(self.config.RATE/2.0), btype='high')
                audio_float = signal.filtfilt(b, a, audio_float)
            except ImportError:
                pass
            
            # Convert back to int16
            return (audio_float * 32768.0).astype(np.int16)
            
        except Exception as e:
            self.logger.error(f"Error in audio preprocessing: {str(e)}")
            return audio_data

    def process_recognition_result(self, recognizer) -> Optional[str]:
        """Process audio with configuration-based thresholds."""
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if text:
            # Don't return single-word responses unless they're common expressions
            if len(text.split()) > 1 or text.lower() in {'yes', 'no', 'okay', 'thanks'}:
                return text
        return None

    def process_partial_result(self, recognizer) -> Optional[str]:
        """Process partial recognition results."""
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        
        # Use configured thresholds for partial results
        if (partial_text and 
            len(partial_text.split()) > 2 and
            partial_text != self._last_partial):
            
            self._last_partial = partial_text
            return f"(Partial) {partial_text}"
        return None
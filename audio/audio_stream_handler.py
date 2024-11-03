import numpy as np
import pyaudio

class AudioStreamHandler:
    def __init__(self, config, audio_queue, logger):
        self.config = config
        self.audio_queue = audio_queue
        self.logger = logger

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Simplified but robust audio callback."""
        try:
            # Convert to numpy array (maintain int16 format)
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # For stereo, convert to mono
            if self.config.CHANNELS == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            # Simple voice activity detection
            audio_level = np.abs(audio_data).mean() / 32768.0
            if audio_level > self.config.VAD_THRESHOLD:
                self.audio_queue.put(audio_data.copy())
            
            return (None, pyaudio.paContinue)
            
        except Exception as e:
            self.logger.error(f"Error in audio callback: {str(e)}")
            return (None, pyaudio.paComplete)

    def update_speaking_state(self, is_voice: bool, audio_data: np.ndarray, state_data: dict) -> bool:
        """Enhanced speaking state detection with phrase boundary handling."""
        import time
        
        current_time = time.time()
        samples_to_ms = lambda x: (x * 1000) / self.config.RATE
        
        if is_voice:
            state_data['voice_frames'] += len(audio_data)
            state_data['silence_frames'] = 0
            
            if not state_data['is_speaking']:
                if (current_time - state_data['last_phrase_end']) > 0.3:  # 300ms minimum gap
                    state_data['is_speaking'] = True
                    state_data['audio_buffer'] = []
                    self.logger.debug("Started new phrase")
        else:
            state_data['silence_frames'] += len(audio_data)
            
            if state_data['is_speaking']:
                if samples_to_ms(state_data['silence_frames']) > 300:  # 300ms silence
                    if samples_to_ms(state_data['voice_frames']) > 250:  # 250ms minimum phrase
                        state_data['is_speaking'] = False
                        state_data['last_phrase_end'] = current_time
                        self.logger.debug(
                            f"Ended phrase - duration: {samples_to_ms(state_data['voice_frames']):.0f}ms"
                        )
                        return True
        
        if state_data['is_speaking']:
            state_data['audio_buffer'].extend(audio_data)
        
        return False
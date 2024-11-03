import pyaudio

class AudioConfig:
    """
    Audio configuration for Seeed 2-mic.
    
        Attributes:
        RATE (int): The sample rate of the audio. Vosk expects a rate of 16000 and resampling is made.
        CHANNELS (int): The number of channels for the audio input. Seeed 2-mic requires 2 channels.
        CHUNK (int): The size of each chunk of audio data.
        FORMAT (int): The format of the audio data. This is set to pyaudio.paInt16, which is 16-bit signed little-endian.
        DEVICE_INDEX (Optional[int]): The index of the device to use for audio input. This is set to None.
        VAD_THRESHOLD (float): The threshold for voice activity detection.
        SILENCE_THRESHOLD (float): The threshold for silence detection.
        MIN_PHRASE_MS (int): The minimum duration of a valid phrase in milliseconds.
        MAX_PHRASE_MS (int): The maximum duration of a phrase in milliseconds.
        SILENCE_MS (int): The duration of silence required to mark the end of a phrase in milliseconds.
    """
    RATE = 48000  # Changed to 16000 to match Vosk's expected sample rate
    VOSK_RATE = 16000 
    CHANNELS = 2
    CHUNK = 1024  # Reduced chunk size for better responsiveness. Try 8000.
    FORMAT = pyaudio.paInt16 #paFloat32  # Changed to float32 for better audio processing. Try paInt16.
    DEVICE_INDEX = None
    
    VAD_THRESHOLD = 0.003 # Try 0.01
    SILENCE_THRESHOLD = 0.002 # Try 0.01
    MIN_PHRASE_MS = 250  # Minimum milliseconds for a valid phrase
    MAX_PHRASE_MS = 10000  # Maximum milliseconds for a phrase
    SILENCE_MS = 300  # Milliseconds of silence to mark end of phrase
import logging
from typing import Optional
import pyaudio

class AudioDeviceManager:
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.audio = None
        
    def setup_devices(self):
        """Set up audio device focusing on hardware devices."""
        try:
            self.logger.info("\nScanning for audio devices...")
            
            # Look specifically for the Seeed device at hw:0,0
            found_device = False
            
            # Try to open the hardware device directly
            try:
                test_stream = self.audio.open(
                    format=self.config.FORMAT,
                    channels=self.config.CHANNELS,
                    rate=self.config.RATE,
                    input=True,
                    input_device_index=0,  # Try hardware device 0
                    frames_per_buffer=self.config.CHUNK,
                    start=False
                )
                test_stream.close()
                self.config.DEVICE_INDEX = 0
                found_device = True
                self.logger.info("Successfully opened hardware device at index 0")
                return
                
            except Exception as e:
                self.logger.warning(f"Could not open hardware device directly: {e}")
            
            # If direct hardware access failed, try scanning devices
            if not found_device:
                for i in range(self.audio.get_device_count()):
                    try:
                        dev_info = self.audio.get_device_info_by_index(i)
                        name = dev_info.get('name', '').lower()
                        
                        self.logger.info(f"\nChecking device {i}: {name}")
                        
                        # Look for hardware or Seeed device
                        if ('hw:' in name or 'seeed' in name) and dev_info['maxInputChannels'] > 0:
                            try:
                                test_stream = self.audio.open(
                                    format=self.config.FORMAT,
                                    channels=self.config.CHANNELS,
                                    rate=self.config.RATE,
                                    input=True,
                                    input_device_index=i,
                                    frames_per_buffer=self.config.CHUNK,
                                    start=False
                                )
                                test_stream.close()
                                self.config.DEVICE_INDEX = i
                                found_device = True
                                self.logger.info(f"Successfully configured device: {name}")
                                return
                                
                            except Exception as e:
                                self.logger.warning(f"Could not open device {i}: {e}")
                                
                    except Exception as e:
                        self.logger.warning(f"Error checking device {i}: {e}")
            
            if not found_device:
                self.logger.error("\nCould not find working input device!")
                self.logger.error("Please check:")
                self.logger.error("1. Is the Seeed ReSpeaker connected?")
                self.logger.error("2. Run 'arecord -l' to verify device")
                self.logger.error("3. Try: sudo chmod 666 /dev/snd/*")
                self.logger.error("4. Try: sudo usermod -a -G audio $USER")
                raise RuntimeError("No working input device found")
                
        except Exception as e:
            self.logger.error(f"Device setup failed: {str(e)}")
            raise
            
    def log_available_devices(self):
        """Log information about all available audio devices"""
        self.logger.info("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
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
                
    def find_seeed_device(self):
        """Find Seeed ReSpeaker device if available."""
        try:
            for i in range(self.audio.get_device_count()):
                dev_info = self.audio.get_device_info_by_index(i)
                # Look for ReSpeaker in device name (case insensitive)
                if any(name in dev_info['name'].lower() for name in ['seeed', 'respeaker']):
                    if dev_info['maxInputChannels'] > 0:  # Ensure it's an input device
                        return dev_info
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding Seeed device: {str(e)}")
            return None
"""
I2S Audio Driver for Raspberry Pi Pico W

Handles I2S audio output to UDA1334A decoder.
Based on the wiring instructions from README.wiring.
"""

import array
import machine
import uasyncio as asyncio
from machine import Pin
import struct

class I2SDriver:
    """
    I2S Audio Driver for Raspberry Pi Pico W to UDA1334A decoder.
    Handles audio output via I2S protocol.
    """
    
    def __init__(self, bck_pin, ws_pin, sd_pin, sample_rate=44100, 
                 bits=16, channels=2, buffer_size=1024):
        """
        Initialize the I2S audio driver.
        
        Args:
            bck_pin (int): I2S clock pin number
            ws_pin (int): I2S word select pin number
            sd_pin (int): I2S data pin number
            sample_rate (int): Audio sample rate in Hz (default: 44100)
            bits (int): Bit depth (default: 16)
            channels (int): Number of audio channels (default: 2 for stereo)
            buffer_size (int): Audio buffer size in bytes (default: 1024)
        """
        self.bck_pin = bck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin
        self.sample_rate = sample_rate
        self.bits = bits
        self.channels = channels
        self.buffer_size = buffer_size
        
        # Create audio buffer
        self.buffer = array.array('H', [0] * (buffer_size // 2))
        self.buffer_index = 0
        self.buffer_full = False
        
        # Initialize I2S peripheral
        self.i2s = machine.I2S(
            0,                      # I2S peripheral ID
            sck=Pin(bck_pin),       # Serial clock pin
            ws=Pin(ws_pin),         # Word select pin
            sd=Pin(sd_pin),         # Serial data pin
            mode=machine.I2S.TX,    # Transmit mode
            bits=bits,              # Bit depth
            format=machine.I2S.STEREO,  # Audio format
            rate=sample_rate,       # Sample rate
            ibuf=buffer_size        # Internal buffer size
        )
        
        # State tracking
        self.is_playing = False
        self.volume = 1.0  # Volume scaling factor (1.0 = 100%)
        
        # Create lock for buffer access
        self.buffer_lock = asyncio.Lock()
    
    async def start(self):
        """Start audio playback."""
        if not self.is_playing:
            self.is_playing = True
            asyncio.create_task(self._playback_task())
    
    async def stop(self):
        """Stop audio playback."""
        self.is_playing = False
        self.clear_buffer()
    
    async def write(self, data):
        """
        Write audio data to buffer.
        
        Args:
            data (bytes): PCM audio data
        
        Returns:
            bool: True if buffer is full, False otherwise
        """
        async with self.buffer_lock:
            bytes_written = 0
            for i in range(0, len(data), 2):
                if i + 1 < len(data):
                    # Convert bytes to 16-bit sample and apply volume
                    sample = struct.unpack('<h', data[i:i+2])[0]
                    sample = int(sample * self.volume)
                    
                    # Write to buffer
                    if self.buffer_index < len(self.buffer):
                        self.buffer[self.buffer_index] = sample & 0xFFFF
                        self.buffer_index += 1
                        bytes_written += 2
                    else:
                        self.buffer_full = True
                        break
            
            return self.buffer_full
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        for i in range(len(self.buffer)):
            self.buffer[i] = 0
        self.buffer_index = 0
        self.buffer_full = False
    
    def set_volume(self, volume):
        """
        Set the volume level.
        
        Args:
            volume (float): Volume level from 0.0 to 1.0
        """
        if 0.0 <= volume <= 1.0:
            self.volume = volume
    
    async def _playback_task(self):
        """Background task for audio playback."""
        try:
            while self.is_playing:
                if self.buffer_index > 0:
                    async with self.buffer_lock:
                        # Write buffer to I2S
                        self.i2s.write(self.buffer[:self.buffer_index])
                        self.buffer_index = 0
                        self.buffer_full = False
                else:
                    # No data, yield to other tasks
                    await asyncio.sleep_ms(5)
        except Exception as e:
            print(f"I2S playback error: {e}")
            self.is_playing = False
    
    def deinit(self):
        """Deinitialize the I2S driver."""
        try:
            self.is_playing = False
            self.i2s.deinit()
        except:
            pass


def test_i2s_driver(bck_pin=18, ws_pin=19, sd_pin=20):
    """
    Test function for I2S driver.
    Generates a simple sine wave and plays it.
    """
    import math
    import time
    
    # Create I2S driver
    i2s = I2SDriver(bck_pin, ws_pin, sd_pin)
    
    # Generate a simple sine wave (440 Hz tone)
    def generate_sine_wave(frequency=440, duration=1):
        samples_count = int(i2s.sample_rate * duration)
        samples = array.array('h')
        for i in range(samples_count):
            t = i / i2s.sample_rate
            value = int(32767 * math.sin(2 * math.pi * frequency * t))
            samples.append(value)  # Left channel
            samples.append(value)  # Right channel
        return samples
    
    # Convert array to bytes
    sine_wave = generate_sine_wave()
    sine_bytes = bytearray(2 * len(sine_wave))
    for i, sample in enumerate(sine_wave):
        struct.pack_into('<h', sine_bytes, i*2, sample)
    
    async def play_test_tone():
        await i2s.start()
        for i in range(0, len(sine_bytes), 1024):
            chunk = sine_bytes[i:i+1024]
            buffer_full = await i2s.write(chunk)
            if buffer_full:
                await asyncio.sleep_ms(10)
        
        # Let it finish playing
        await asyncio.sleep(1)
        await i2s.stop()
        i2s.deinit()
        print("Test completed")
    
    print("Testing I2S driver with 440 Hz tone...")
    asyncio.run(play_test_tone())


if __name__ == "__main__":
    # Run the test
    test_i2s_driver() 
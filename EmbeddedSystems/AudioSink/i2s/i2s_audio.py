"""
I2S Audio Driver for UDA1334A

This module provides an interface to the UDA1334A I2S Stereo Decoder.
It handles sending audio data via I2S protocol from the Raspberry Pi Pico W.
"""

import uasyncio as asyncio
from machine import Pin, PWM, I2S
from micropython import const
import time
from ble_config import *

# I2S configuration
I2S_ID = 0  # I2S peripheral ID
SCK_PIN = GPIO_I2S_SCK
WS_PIN = GPIO_I2S_WS
SD_PIN = GPIO_I2S_SD
MUTE_PIN = GPIO_MUTE  # UDA1334A mute pin

# Audio format
BITS_PER_SAMPLE = 16
BITS_PER_FRAME = BITS_PER_SAMPLE * 2  # stereo = 2 channels
SAMPLE_BUFFER_SIZE = 1024  # Number of audio samples in the buffer

class I2SAudio:
    def __init__(self, 
                 sample_rate=AUDIO_SAMPLE_RATE,
                 buffer_size=SAMPLE_BUFFER_SIZE):
        """Initialize I2S audio interface."""
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._is_playing = False
        self._is_paused = False
        self._audio_buffer = bytearray()
        self._buffer_lock = asyncio.Lock()
        
        # Configure mute pin
        self._mute_pin = Pin(MUTE_PIN, Pin.OUT)
        self._set_mute(True)  # Start muted
        
        # Configure I2S
        self._i2s = None
        self._initialize_i2s()
        
        # Status callback
        self._status_callback = None

    def _initialize_i2s(self):
        """Initialize the I2S interface."""
        try:
            self._i2s = I2S(
                I2S_ID,
                sck=Pin(SCK_PIN),
                ws=Pin(WS_PIN),
                sd=Pin(SD_PIN),
                mode=I2S.TX,
                bits=BITS_PER_SAMPLE,
                format=I2S.STEREO,
                rate=self._sample_rate,
                ibuf=self._buffer_size
            )
            print(f"I2S initialized: {self._sample_rate}Hz, {BITS_PER_SAMPLE}-bit")
            return True
        except Exception as e:
            print(f"I2S initialization failed: {e}")
            return False

    def set_status_callback(self, callback):
        """Set a callback for status updates."""
        self._status_callback = callback
    
    def set_sample_rate(self, sample_rate):
        """Change the sample rate."""
        was_playing = self._is_playing and not self._is_paused
        
        # Stop playing if active
        if was_playing:
            self.stop()
        
        # Deinitialize and reinitialize with new rate
        if self._i2s:
            self._i2s.deinit()
        
        self._sample_rate = sample_rate
        success = self._initialize_i2s()
        
        # Resume playback if it was active
        if was_playing and success:
            self.play()
        
        return success
    
    def _set_mute(self, mute):
        """Set the mute state of the UDA1334A."""
        if mute:
            self._mute_pin.value(1)  # Muted
        else:
            self._mute_pin.value(0)  # Unmuted
    
    async def add_audio_data(self, data):
        """Add audio data to the buffer."""
        async with self._buffer_lock:
            self._audio_buffer.extend(data)
        
        # Start playback if not already playing and buffer has enough data
        if not self._is_playing and len(self._audio_buffer) >= self._buffer_size * 2:
            self.play()
    
    def play(self):
        """Start or resume audio playback."""
        if not self._is_playing:
            self._is_playing = True
            self._is_paused = False
            self._set_mute(False)
            asyncio.create_task(self._playback_task())
            
            if self._status_callback:
                self._status_callback(STATUS_PLAYING)
            return True
        
        elif self._is_paused:
            self._is_paused = False
            self._set_mute(False)
            
            if self._status_callback:
                self._status_callback(STATUS_PLAYING)
            return True
        
        return False
    
    def pause(self):
        """Pause audio playback."""
        if self._is_playing and not self._is_paused:
            self._is_paused = True
            self._set_mute(True)
            
            if self._status_callback:
                self._status_callback(STATUS_PAUSED)
            return True
        return False
    
    def stop(self):
        """Stop audio playback and clear buffer."""
        if self._is_playing:
            self._is_playing = False
            self._is_paused = False
            self._set_mute(True)
            
            # Clear buffer
            async def clear_buffer():
                async with self._buffer_lock:
                    self._audio_buffer = bytearray()
            
            asyncio.create_task(clear_buffer())
            
            if self._status_callback:
                self._status_callback(STATUS_STOPPED)
            return True
        return False
    
    def is_playing(self):
        """Check if audio is currently playing."""
        return self._is_playing and not self._is_paused
    
    def is_paused(self):
        """Check if audio is currently paused."""
        return self._is_playing and self._is_paused
    
    def get_buffer_level(self):
        """Get the current buffer fill level (percentage)."""
        if not self._buffer_size:
            return 0
        
        buffer_len = len(self._audio_buffer)
        max_buffer = self._buffer_size * 4  # Maximum buffer size (bytes)
        
        return min(100, int(buffer_len * 100 / max_buffer))
    
    async def _playback_task(self):
        """Background task for continuous playback."""
        try:
            while self._is_playing:
                if self._is_paused:
                    # When paused, just wait
                    await asyncio.sleep(0.1)
                    continue
                
                # Get data chunk from buffer
                data_chunk = None
                async with self._buffer_lock:
                    if len(self._audio_buffer) >= self._buffer_size:
                        # Get a chunk of data
                        data_chunk = self._audio_buffer[:self._buffer_size]
                        # Remove the chunk from buffer
                        self._audio_buffer = self._audio_buffer[self._buffer_size:]
                
                if data_chunk:
                    # Write data to I2S
                    self._i2s.write(data_chunk)
                else:
                    # Buffer underrun
                    if self._is_playing:
                        print("Audio buffer underrun")
                        # Small pause to avoid busy loop
                        await asyncio.sleep(0.01)
                        
                        # If buffer is completely empty, stop playback
                        if len(self._audio_buffer) == 0:
                            self.stop()
                            break
                
                # Give other tasks a chance to run
                await asyncio.sleep(0)
                
        except Exception as e:
            print(f"Playback error: {e}")
            self._set_mute(True)
            self._is_playing = False
            if self._status_callback:
                self._status_callback(STATUS_ERROR)
    
    def deinit(self):
        """Deinitialize the I2S interface."""
        if self._is_playing:
            self.stop()
        
        if self._i2s:
            self._i2s.deinit()
            self._i2s = None
        
        self._set_mute(True)
        print("I2S audio deinitialized")


# Test function for the I2S audio interface
async def test_i2s_audio():
    """Test the I2S audio interface with a sine wave."""
    import math
    
    audio = I2SAudio()
    
    # Create a simple sine wave for testing (1kHz tone)
    def generate_sine_wave(freq=1000, duration_ms=1000):
        samples = []
        sample_count = (AUDIO_SAMPLE_RATE * duration_ms) // 1000
        for i in range(sample_count):
            # Calculate sine wave value between -1.0 and 1.0
            value = math.sin(2 * math.pi * freq * i / AUDIO_SAMPLE_RATE)
            # Convert to 16-bit signed int (-32768 to 32767)
            int_value = int(value * 32767)
            # Add sample for left and right channel
            samples.append(int_value)
            samples.append(int_value)
        
        # Convert to byte array
        result = bytearray(len(samples) * 2)
        for i, sample in enumerate(samples):
            # Convert 16-bit signed ints to bytes (little endian)
            result[i*2] = sample & 0xFF
            result[i*2+1] = (sample >> 8) & 0xFF
        
        return result
    
    # Generate a test tone
    test_tone = generate_sine_wave(freq=440, duration_ms=1000)  # 440Hz (A4) for 1 second
    
    print("Playing test tone...")
    await audio.add_audio_data(test_tone)
    
    # Let it play for a bit
    await asyncio.sleep(2)
    
    # Test pause and resume
    print("Pausing...")
    audio.pause()
    await asyncio.sleep(1)
    
    print("Resuming...")
    audio.play()
    await asyncio.sleep(1)
    
    # Test stop
    print("Stopping...")
    audio.stop()
    
    # Clean up
    audio.deinit()
    print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_i2s_audio()) 
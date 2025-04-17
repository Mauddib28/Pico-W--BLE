"""
audio_config.py - Audio Processing Configuration

This module contains configuration settings and constants for the
audio processing implementation.
"""

from micropython import const
import array

# Audio format configuration
AUDIO_FORMAT_PCM = const(0x01)
AUDIO_FORMAT_MP3 = const(0x02)
AUDIO_FORMAT_AAC = const(0x03)

# Audio buffer configuration
AUDIO_BUFFER_SIZE = const(512)    # Size of audio buffer in bytes
AUDIO_BUFFER_COUNT = const(4)     # Number of audio buffers to use

# Audio playback states
PLAYBACK_IDLE = const(0)
PLAYBACK_PLAYING = const(1)
PLAYBACK_PAUSED = const(2)
PLAYBACK_STOPPED = const(3)

# Volume control
VOLUME_MIN = const(0)
VOLUME_MAX = const(100)
VOLUME_DEFAULT = const(80)

# Circular buffer implementation for audio
class AudioBuffer:
    def __init__(self, buffer_size=AUDIO_BUFFER_SIZE, buffer_count=AUDIO_BUFFER_COUNT):
        """Initialize audio buffer system"""
        self.buffers = [bytearray(buffer_size) for _ in range(buffer_count)]
        self.buffer_sizes = [0] * buffer_count
        self.write_index = 0
        self.read_index = 0
        self.count = 0
        self.max_count = buffer_count
    
    def push(self, data, length):
        """Add data to buffer"""
        if self.count >= self.max_count:
            return False  # Buffer full
        
        # Copy data to current write buffer
        buffer = self.buffers[self.write_index]
        copy_len = min(length, len(buffer))
        for i in range(copy_len):
            buffer[i] = data[i]
        
        self.buffer_sizes[self.write_index] = copy_len
        self.write_index = (self.write_index + 1) % self.max_count
        self.count += 1
        return True
    
    def pop(self):
        """Get data from buffer"""
        if self.count <= 0:
            return None, 0  # Buffer empty
        
        buffer = self.buffers[self.read_index]
        size = self.buffer_sizes[self.read_index]
        self.read_index = (self.read_index + 1) % self.max_count
        self.count -= 1
        return buffer, size
    
    def clear(self):
        """Clear all buffers"""
        self.write_index = 0
        self.read_index = 0
        self.count = 0

# Global audio buffer
audio_buffer = AudioBuffer()

# Function declarations
def init_audio_processing():
    """Initialize audio processing"""
    pass

def process_audio_packet(data, length):
    """Process incoming audio packet"""
    # Add to buffer
    return audio_buffer.push(data, length)

def start_audio_playback():
    """Start audio playback"""
    pass

def pause_audio_playback():
    """Pause audio playback"""
    pass

def resume_audio_playback():
    """Resume audio playback"""
    pass

def stop_audio_playback():
    """Stop audio playback"""
    audio_buffer.clear()

def set_audio_volume(volume_level):
    """Set audio volume"""
    # Ensure volume is within range
    return max(VOLUME_MIN, min(VOLUME_MAX, volume_level))

def generate_test_tone(buffer, length):
    """Generate a test tone"""
    # Generate a simple sine wave test tone
    import math
    
    frequency = 440  # A4 note
    amplitude = 0.5  # Half volume
    
    # For 16-bit stereo
    if length % 4 != 0:
        length = length - (length % 4)  # Ensure length is multiple of 4
        
    samples = length // 4  # 2 bytes per sample, 2 channels
    
    for i in range(samples):
        # Calculate sine wave value for this sample
        value = int(32767 * amplitude * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE))
        
        # Set left and right channel to same value
        idx = i * 4
        # Low byte
        buffer[idx] = value & 0xFF
        buffer[idx + 2] = value & 0xFF
        # High byte
        buffer[idx + 1] = (value >> 8) & 0xFF
        buffer[idx + 3] = (value >> 8) & 0xFF 
"""
BLE Audio Sink - Audio Processing Module

This module handles the audio data processing and I2S output,
including buffering, playback control, and communication with
the I2S interface.
"""

import struct
import time
import array
from machine import Pin, I2S
from micropython import const

from .ble_config import *

# Audio state
_is_playing = False
_is_paused = False
_buffer_underrun = False

# I2S interface
_i2s = None

# Audio buffers and statistics
_audio_buffer = []
_buffer_size = 0
_buffer_target = AUDIO_BUFFER_TARGET_MS
_packet_count = 0
_last_sequence = 0
_buffer_stats = {
    'underruns': 0,
    'overruns': 0,
    'packets_received': 0,
    'packets_played': 0,
    'last_timestamp': 0
}

def init():
    """Initialize the audio subsystem"""
    global _i2s
    
    # Configure I2S pins
    sck_pin = Pin(I2S_SCK_PIN)
    ws_pin = Pin(I2S_WS_PIN)
    sd_pin = Pin(I2S_SD_PIN)
    
    # Initialize I2S interface
    _i2s = I2S(
        0,                      # I2S peripheral ID
        sck=sck_pin,            # Serial clock
        ws=ws_pin,              # Word select
        sd=sd_pin,              # Serial data
        mode=I2S.TX,            # Transmit mode
        bits=AUDIO_BIT_DEPTH,   # Bit depth
        format=I2S.STEREO,      # Audio format
        rate=AUDIO_SAMPLE_RATE, # Sample rate
        ibuf=AUDIO_I2S_BUFFER   # Internal buffer size
    )
    
    # Reset buffer
    reset_buffer()
    
    print(f"Audio initialized: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_BIT_DEPTH}bit")
    return True

def process_audio_data(data):
    """Process incoming audio data from BLE"""
    global _audio_buffer, _buffer_size, _last_sequence, _packet_count
    global _buffer_stats
    
    # Validate data
    if len(data) < 3:  # At least seq number + 1 sample
        return
    
    # Extract sequence number (first 2 bytes)
    sequence = struct.unpack('<H', data[0:2])[0]
    
    # Check for packet loss
    if _packet_count > 0 and sequence != (_last_sequence + 1) % 65536:
        # Calculate lost packets
        if sequence > _last_sequence:
            lost = sequence - _last_sequence - 1
        else:
            # Handle wrap-around
            lost = (65536 - _last_sequence - 1) + sequence
            
        print(f"Packet loss detected: {lost} packets missing")
    
    _last_sequence = sequence
    _packet_count += 1
    _buffer_stats['packets_received'] += 1
    _buffer_stats['last_timestamp'] = time.ticks_ms()
    
    # Extract audio data (skip first 2 bytes which are sequence number)
    audio_data = data[2:]
    
    # Add to buffer
    _audio_buffer.append(audio_data)
    _buffer_size += len(audio_data)
    
    # If paused or stopped, don't start automatically
    if not _is_playing and not _is_paused:
        # If buffer is full enough, start playback
        if _buffer_size >= _buffer_target:
            start_playback()

def _play_audio_task():
    """Background task to play audio from buffer"""
    global _audio_buffer, _buffer_size, _is_playing, _buffer_underrun
    global _buffer_stats
    
    if not _is_playing or _is_paused:
        return
    
    # If buffer is empty, handle underrun
    if len(_audio_buffer) == 0:
        if not _buffer_underrun:
            print("Buffer underrun")
            _buffer_underrun = True
            _buffer_stats['underruns'] += 1
            
            # Output silence for now
            zeros = bytearray(AUDIO_CHUNK_SIZE)
            _i2s.write(zeros)
        return
    
    # Reset underrun flag
    _buffer_underrun = False
    
    # Get next audio chunk from buffer
    chunk = _audio_buffer.pop(0)
    _buffer_size -= len(chunk)
    _buffer_stats['packets_played'] += 1
    
    # Write to I2S
    try:
        bytes_written = _i2s.write(chunk)
        if bytes_written != len(chunk):
            print(f"I2S write incomplete: {bytes_written}/{len(chunk)} bytes")
    except Exception as e:
        print(f"I2S write error: {e}")

def start_playback():
    """Start audio playback"""
    global _is_playing, _is_paused
    
    if _is_playing and not _is_paused:
        return  # Already playing
    
    _is_playing = True
    _is_paused = False
    print("Audio playback started")
    
    # Schedule the audio task to run regularly
    import _thread
    _thread.start_new_thread(_playback_thread, ())

def _playback_thread():
    """Background thread for audio playback"""
    global _is_playing
    
    while _is_playing:
        _play_audio_task()
        # Sleep to yield CPU time (adjust as needed for performance)
        time.sleep_ms(5)

def pause_playback():
    """Pause audio playback"""
    global _is_paused
    
    if not _is_playing:
        return
    
    _is_paused = True
    print("Audio playback paused")

def stop_playback():
    """Stop audio playback and clear buffer"""
    global _is_playing, _is_paused
    
    _is_playing = False
    _is_paused = False
    reset_buffer()
    print("Audio playback stopped")

def reset_buffer():
    """Reset audio buffer"""
    global _audio_buffer, _buffer_size, _packet_count, _last_sequence
    
    _audio_buffer = []
    _buffer_size = 0
    _packet_count = 0
    _last_sequence = 0
    
    print("Audio buffer reset")

def get_buffer_level():
    """Get current buffer fullness level (percent)"""
    if _buffer_target == 0:
        return 0
    return min(100, int((_buffer_size * 100) / _buffer_target))

def get_stats():
    """Get audio statistics"""
    stats = _buffer_stats.copy()
    stats['buffer_level'] = get_buffer_level()
    stats['is_playing'] = _is_playing
    stats['is_paused'] = _is_paused
    stats['buffer_size'] = _buffer_size
    return stats

def deinit():
    """Deinitialize the audio subsystem"""
    global _i2s, _is_playing
    
    # Stop playback
    _is_playing = False
    time.sleep_ms(50)  # Give playback thread time to stop
    
    # Deinitialize I2S
    if _i2s:
        _i2s.deinit()
        _i2s = None
    
    print("Audio deinitialized")
    return True 
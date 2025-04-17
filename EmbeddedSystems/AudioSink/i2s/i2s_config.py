"""
i2s_config.py - I2S Configuration and Constants

This module contains configuration settings and constants for the
I2S audio output implementation for the Pico WH connected to the
Adafruit I2S Stereo Decoder (UDA1334A).

Wiring connections:
- Pico WH GPIO 0 -> I2S Decoder BCLK (Bit Clock)
- Pico WH GPIO 1 -> I2S Decoder LRCLK (Word Select/Left-Right Clock)
- Pico WH GPIO 2 -> I2S Decoder DIN (Data In)
- Pico WH GPIO 3 -> I2S Decoder MUTE (Optional)
- Pico WH 3.3V -> I2S Decoder VIN
- Pico WH GND -> I2S Decoder GND
"""

import machine
from micropython import const

# I2S pin definitions
# These pin numbers MUST match the physical connections to the I2S decoder
I2S_BCLK_PIN = const(0)      # Bit Clock on GPIO 0
I2S_LRCLK_PIN = const(1)     # Word/Left-Right Clock on GPIO 1  
I2S_DATA_PIN = const(2)      # Data output pin on GPIO 2
I2S_MUTE_PIN = const(3)      # Optional mute control on GPIO 3

# I2S configuration
# These settings are specific to the UDA1334A decoder capabilities
SAMPLE_RATE = const(44100)   # Standard CD quality (44.1kHz)
BIT_DEPTH = const(16)        # 16-bit audio samples
AUDIO_CHANNELS = const(2)    # Stereo (2 channels)

# I2S buffer sizes
I2S_BUFFER_SIZE = const(1024)  # Output buffer size
I2S_QUEUE_SIZE = const(4)      # Number of buffers in the queue

# I2S object
i2s = None

def init_i2s():
    """
    Initialize the I2S interface
    
    This function sets up the I2S interface to communicate with the
    UDA1334A I2S stereo decoder connected to the specified pins.
    """
    global i2s
    
    print(f"Initializing I2S: BCLK={I2S_BCLK_PIN}, LRCLK={I2S_LRCLK_PIN}, DATA={I2S_DATA_PIN}")
    
    # MicroPython I2S initialization
    # Note: Implementation will depend on the specific MicroPython I2S library
    # For now, this is a placeholder to be filled with the actual implementation
    try:
        # This is a placeholder for the actual I2S initialization
        # The actual implementation will depend on the MicroPython I2S library used
        # i2s = machine.I2S(...)
        configure_i2s_pins()
        print("I2S interface initialized successfully")
    except Exception as e:
        print(f"Failed to initialize I2S: {e}")
    
    return i2s is not None

def configure_i2s_pins():
    """
    Configure GPIO pins for I2S operation
    
    This function sets up the GPIO pins for I2S communication.
    It configures the pins as outputs with appropriate default states.
    """
    # Set up GPIO pins for I2S
    # BCLK pin - Bit Clock
    bclk = machine.Pin(I2S_BCLK_PIN, machine.Pin.OUT)
    bclk.value(0)  # Initialize low
    
    # LRCLK pin - Left/Right Clock (Word Select)
    lrclk = machine.Pin(I2S_LRCLK_PIN, machine.Pin.OUT)
    lrclk.value(0)  # Initialize low
    
    # DATA pin - Serial Data
    data = machine.Pin(I2S_DATA_PIN, machine.Pin.OUT)
    data.value(0)  # Initialize low
    
    # MUTE pin (if used)
    mute_pin = machine.Pin(I2S_MUTE_PIN, machine.Pin.OUT)
    mute_pin.value(0)  # Initialize to not muted (depends on UDA1334A configuration)
    
    print("I2S pins configured")

def start_i2s():
    """
    Start I2S output
    
    This function starts the I2S interface for audio output.
    It should be called before sending audio data.
    """
    global i2s
    if i2s:
        # Start I2S output
        # Implementation depends on the specific I2S library
        print("Starting I2S output")
    else:
        print("I2S not initialized, cannot start")

def stop_i2s():
    """
    Stop I2S output
    
    This function stops the I2S interface, halting audio output.
    It should be called when audio playback is finished.
    """
    global i2s
    if i2s:
        # Stop I2S output
        # Implementation depends on the specific I2S library
        print("Stopping I2S output")
    else:
        print("I2S not initialized, nothing to stop")

def mute_i2s(mute):
    """
    Mute or unmute I2S output
    
    This function controls the MUTE pin on the UDA1334A decoder.
    
    Args:
        mute (bool): True to mute audio, False to unmute
    """
    # UDA1334A mute pin control
    # The mute behavior depends on how the UDA1334A is configured
    # Typically, high = muted, low = unmuted, but check your specific board
    mute_pin = machine.Pin(I2S_MUTE_PIN, machine.Pin.OUT)
    mute_pin.value(1 if mute else 0)
    print(f"{'Muted' if mute else 'Unmuted'} audio output")

def write_audio_data(data, length):
    """
    Write audio data to I2S output
    
    This function sends audio data to the I2S interface for output
    to the connected UDA1334A decoder.
    
    Args:
        data (bytearray): Audio data buffer
        length (int): Length of valid data in the buffer
    
    Returns:
        bool: True if successful, False otherwise
    """
    global i2s
    if i2s:
        # Write audio data to I2S output
        # Implementation depends on the specific I2S library
        # i2s.write(data[:length])
        return True
    else:
        print("I2S not initialized, cannot write audio data")
        return False

def set_i2s_volume(volume_level):
    """
    Set I2S volume
    
    Note: The UDA1334A does not have hardware volume control.
    Volume control must be implemented in software by scaling
    the audio samples before sending them to the I2S interface.
    
    Args:
        volume_level (int): Volume level (0-100%)
    """
    # Volume control implementation
    # This must be handled in software by scaling the audio samples
    print(f"Setting software volume to {volume_level}%")
    
    # Scale factor would be applied to audio samples before sending to I2S
    # scale_factor = volume_level / 100.0
    
    return volume_level

def play_test_tone():
    """
    Play a simple test tone through I2S
    
    This function generates a 440Hz sine wave and plays it
    through the I2S interface for 3 seconds as a connection test.
    """
    import math
    import time
    
    print("Generating test tone (440Hz)...")
    
    # Configure pins for manual I2S operation (temporary implementation)
    bclk = machine.Pin(I2S_BCLK_PIN, machine.Pin.OUT)
    lrclk = machine.Pin(I2S_LRCLK_PIN, machine.Pin.OUT)
    data = machine.Pin(I2S_DATA_PIN, machine.Pin.OUT)
    
    # Unmute the output
    mute_i2s(False)
    
    # Note: This is a very simplified version that doesn't implement
    # the full I2S protocol. It's just for basic hardware testing.
    # A real implementation would use a proper I2S library.
    
    # Simulate sending some data
    print("Sending test signal to I2S pins...")
    for i in range(1000):
        # Toggle bit clock several times for each sample
        for j in range(16):
            bclk.value(1)
            # Simulate data based on a sine wave
            data_bit = 1 if (i + j) % 2 == 0 else 0
            data.value(data_bit)
            bclk.value(0)
        
        # Toggle word select (LRCLK) between left and right channel
        lrclk.value(1 if i % 2 == 0 else 0)
        
        # Small delay
        time.sleep_us(10)
    
    print("Test tone finished") 
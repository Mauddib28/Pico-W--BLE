"""
Bluetooth Audio Speaker/Headset - Main Script

This script implements a BLE Audio Sink device using a Pico WH and
Adafruit I2S Stereo Decoder (UDA1334A).

It enables audio data transmission over BLE protocol to the Pico WH,
which then sends the audio to speakers/headphones via the I2S Decoder.

Hardware:
- Raspberry Pi Pico WH
- Adafruit I2S Stereo Decoder - UDA1334A

Dependencies:
- MicroPython BLE libraries
- MicroPython I2S libraries

Pin Connections:
- See README.wiring for detailed wiring information
"""

import time
import machine
import bluetooth
from ble.ble_config import *
from ble.ble_device import init_ble, start_advertising, stop_advertising, is_connected, update_status
from audio.audio_config import *
from i2s.i2s_config import *
from serial.serial_interface import *

# I2S pin definitions
I2S_BCLK_PIN = 0      # Bit Clock
I2S_LRCLK_PIN = 1     # Word/Left-Right Clock
I2S_DATA_PIN = 2      # Data pin
I2S_MUTE_PIN = 3      # Optional mute control (connect to GND to mute)

# I2S configuration
SAMPLE_RATE = 44100   # Standard CD quality
BIT_DEPTH = 16        # 16-bit audio

# BLE device information
BLE_DEVICE_NAME = "BLE Audio Sink"
BLE_DEVICE_ALIAS = "BLE I2S"

# Audio buffer configuration
AUDIO_BUFFER_SIZE = 512  # Size of audio buffer in bytes

# Global variables
is_playing = False
volume = 100  # 0-100%
audio_buffer = bytearray(AUDIO_BUFFER_SIZE)

def setup_ble():
    """Initialize the BLE interface"""
    print("Setting up BLE...")
    
    # Initialize BLE stack
    if not init_ble():
        print("Failed to initialize BLE, retrying...")
        time.sleep(1)
        if not init_ble():
            print("BLE initialization failed. Check hardware.")
            return False
    
    # Start advertising our services
    if not start_advertising():
        print("Failed to start advertising, retrying...")
        time.sleep(1)
        if not start_advertising():
            print("BLE advertising failed to start.")
            return False
    
    # Update initial status
    update_status(STATUS_READY)
    
    return True

def setup_i2s():
    """Initialize the I2S interface for audio output"""
    print("Setting up I2S interface...")
    
    # Create a Pin object for the mute control
    mute_pin = machine.Pin(I2S_MUTE_PIN, machine.Pin.OUT)
    mute_pin.value(1)  # Set high to enable audio (active low mute)
    
    # Additional I2S setup will be added in future tasks
    
    return True

def setup_serial_interface():
    """Initialize the serial command interface"""
    print("Setting up serial interface...")
    
    # UART setup will be added in future tasks
    
    return True

def process_audio_data(data, length):
    """Process incoming audio data and send to I2S output"""
    global is_playing
    
    # To be implemented in future tasks
    # This will take BLE received audio data and send it to the I2S output
    
    # For now, just update status
    if not is_playing:
        is_playing = True
        update_status(STATUS_PLAYING)

def handle_ble_events():
    """Handle BLE events (connections, disconnections, data)"""
    # Most BLE events are handled by the IRQ handler in ble_device.py
    
    # Check connection status and update device state if needed
    if is_connected():
        # Connection is active, could perform additional tasks here
        pass
    else:
        # No connection, reset playback state if needed
        global is_playing
        if is_playing:
            is_playing = False
            update_status(STATUS_READY)

def handle_serial_commands():
    """Handle serial commands from user"""
    # To be implemented in future tasks
    # This will process commands from the serial interface
    pass

def main():
    """Main function to initialize and run the program"""
    print("BLE Audio Sink starting...")
    
    # Setup I2S interface
    if not setup_i2s():
        print("I2S setup failed. Check hardware connections.")
        return
    
    # Setup BLE interface
    if not setup_ble():
        print("BLE setup failed. Check hardware.")
        return
    
    # Setup Serial command interface
    if not setup_serial_interface():
        print("Serial interface setup failed.")
        # Non-critical, continue
    
    print("BLE Audio Sink ready!")
    
    # Main loop
    try:
        while True:
            # Handle BLE events (connections, data reception)
            handle_ble_events()
            
            # Handle serial commands
            handle_serial_commands()
            
            # Small delay to prevent CPU hogging
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Clean shutdown
        stop_advertising()

if __name__ == "__main__":
    main() 
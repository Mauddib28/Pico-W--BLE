"""
Test script for BLE Audio Sink

This script provides functions to test various components of the BLE Audio Sink.
"""

import uasyncio as asyncio
import math
import struct
import time
from machine import Pin

# Import components to test
from audio.i2s_driver import I2SDriver, test_i2s_driver
from ble.ble_core import BLEAudioSink, test_ble_audio_sink
from audio.ble_audio_adapter import BLEAudioAdapter, test_ble_audio_adapter
from config import (
    I2S_BCK_PIN, I2S_WS_PIN, I2S_SD_PIN,
    AUDIO_SAMPLE_RATE, AUDIO_BIT_DEPTH, AUDIO_CHANNELS, AUDIO_BUFFER_SIZE,
    STATUS_LED_PIN
)

# Status LED for test indication
status_led = Pin(STATUS_LED_PIN, Pin.OUT)


def blink_led(times=3, interval=0.2):
    """Blink the status LED to indicate test status."""
    for _ in range(times):
        status_led.value(1)
        time.sleep(interval)
        status_led.value(0)
        time.sleep(interval)


async def generate_test_audio(duration=5, frequency=440):
    """
    Generate test audio data (sine wave) for testing.
    
    Args:
        duration (float): Duration in seconds
        frequency (int): Frequency in Hz
        
    Returns:
        bytes: Audio data as bytes
    """
    # Calculate parameters
    sample_rate = AUDIO_SAMPLE_RATE
    num_samples = int(duration * sample_rate)
    
    # Create a buffer for the audio data
    if AUDIO_CHANNELS == 2:
        # Stereo
        buffer = bytearray(num_samples * 4)  # 2 bytes per sample, 2 channels
        
        # Generate a sine wave
        for i in range(num_samples):
            t = i / sample_rate
            value = int(32767 * math.sin(2 * math.pi * frequency * t))
            
            # Pack the value as signed 16-bit (little-endian) for both channels
            struct.pack_into("<hh", buffer, i * 4, value, value)
    else:
        # Mono
        buffer = bytearray(num_samples * 2)  # 2 bytes per sample
        
        # Generate a sine wave
        for i in range(num_samples):
            t = i / sample_rate
            value = int(32767 * math.sin(2 * math.pi * frequency * t))
            
            # Pack the value as signed 16-bit (little-endian)
            struct.pack_into("<h", buffer, i * 2, value)
    
    return buffer


async def test_i2s_basic():
    """Test basic I2S functionality with a sine wave."""
    print("\n===== Testing basic I2S output =====")
    
    # Initialize I2S driver
    i2s = I2SDriver(
        bck_pin=I2S_BCK_PIN,
        ws_pin=I2S_WS_PIN,
        sd_pin=I2S_SD_PIN
    )
    
    # Start I2S
    await i2s.start()
    
    print("Generating test audio...")
    audio_data = await generate_test_audio(3, 440)  # A4 note for 3 seconds
    
    print("Playing test tone (440Hz)...")
    # Send data in chunks
    chunk_size = 1024
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        await i2s.write(chunk)
        await asyncio.sleep(0.01)
    
    # Wait for playback to finish
    await asyncio.sleep(1)
    
    # Try a different frequency
    print("Playing test tone (880Hz)...")
    audio_data = await generate_test_audio(3, 880)  # A5 note for 3 seconds
    
    # Send data in chunks
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        await i2s.write(chunk)
        await asyncio.sleep(0.01)
    
    # Wait for playback to finish
    await asyncio.sleep(1)
    
    # Stop I2S
    await i2s.stop()
    
    print("I2S basic test completed")
    return True


async def test_tone_sequence():
    """Test a sequence of tones to verify I2S output."""
    print("\n===== Testing tone sequence =====")
    
    # Initialize I2S driver
    i2s = I2SDriver(
        bck_pin=I2S_BCK_PIN,
        ws_pin=I2S_WS_PIN,
        sd_pin=I2S_SD_PIN
    )
    
    # Start I2S
    await i2s.start()
    
    # Define a sequence of notes (frequency in Hz, duration in seconds)
    notes = [
        (262, 0.3),  # C4
        (294, 0.3),  # D4
        (330, 0.3),  # E4
        (349, 0.3),  # F4
        (392, 0.3),  # G4
        (440, 0.3),  # A4
        (494, 0.3),  # B4
        (523, 0.5),  # C5
    ]
    
    # Play the sequence
    for frequency, duration in notes:
        print(f"Playing note: {frequency}Hz")
        audio_data = await generate_test_audio(duration, frequency)
        
        # Send data in chunks
        chunk_size = 512
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            await i2s.write(chunk)
            await asyncio.sleep(0.01)
        
        # Small gap between notes
        await asyncio.sleep(0.05)
    
    # Stop I2S
    await i2s.stop()
    
    print("Tone sequence test completed")
    return True


def run_test(test_function):
    """Run a test function in the asyncio event loop."""
    loop = asyncio.get_event_loop()
    
    print(f"Starting test: {test_function.__name__}")
    blink_led(times=2, interval=0.1)
    
    try:
        # Run the test
        result = loop.run_until_complete(test_function())
        
        # Indicate success
        if result:
            print(f"Test {test_function.__name__} PASSED")
            blink_led(times=3, interval=0.1)
        else:
            print(f"Test {test_function.__name__} FAILED")
            blink_led(times=5, interval=0.1)
            
    except Exception as e:
        print(f"Test {test_function.__name__} FAILED with exception: {e}")
        blink_led(times=10, interval=0.05)


def run_all_tests():
    """Run all tests in sequence."""
    print("\n===== Running all tests =====")
    
    try:
        # Run individual component tests
        run_test(test_i2s_basic)
        run_test(test_tone_sequence)
        
        # Run full adapter test (this will run indefinitely)
        run_test(lambda: test_ble_audio_adapter())
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    finally:
        # Turn off LED
        status_led.value(0)


def run_interactive_menu():
    """Run an interactive menu for selecting tests."""
    while True:
        print("\n===== BLE Audio Sink Test Menu =====")
        print("1. Test I2S basic output")
        print("2. Test tone sequence")
        print("3. Test full BLE Audio Adapter")
        print("4. Run I2S driver test")
        print("5. Run BLE core test")
        print("6. Run all tests")
        print("0. Exit")
        
        try:
            choice = input("Enter your choice: ")
            
            if choice == '1':
                run_test(test_i2s_basic)
            elif choice == '2':
                run_test(test_tone_sequence)
            elif choice == '3':
                run_test(lambda: test_ble_audio_adapter())
            elif choice == '4':
                test_i2s_driver()
            elif choice == '5':
                test_ble_audio_sink()
            elif choice == '6':
                run_all_tests()
            elif choice == '0':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("\n===== BLE Audio Sink Test Script =====")
    print("1. Run all tests automatically")
    print("2. Run interactive test menu")
    print("0. Exit")
    
    try:
        choice = input("Enter your choice: ")
        
        if choice == '1':
            run_all_tests()
        elif choice == '2':
            run_interactive_menu()
        else:
            print("Exiting...")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Turn off LED
        status_led.value(0) 
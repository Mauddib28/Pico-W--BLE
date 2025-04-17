"""
Test functions for the BLE Audio Sink.

Contains tests for I2S output and BLE components.
"""

import time
import math
import struct
import array
import uasyncio as asyncio
import gc

from machine import Pin
from audio.i2s_driver import I2SDriver, test_i2s_driver
from ble.ble_core import BLEAudioSink, test_ble_audio_sink
from audio.ble_audio_adapter import BLEAudioAdapter, test_ble_audio_adapter
from config import (
    I2S_BCK_PIN, I2S_WS_PIN, I2S_SD_PIN,
    AUDIO_SAMPLE_RATE, AUDIO_BIT_DEPTH, AUDIO_CHANNELS,
    STATUS_LED_PIN
)

# Configure status LED
status_led = Pin(STATUS_LED_PIN, Pin.OUT)


def blink_led(times=3, interval=0.2):
    """Blink the status LED to indicate test status."""
    for _ in range(times):
        status_led.value(1)
        time.sleep(interval)
        status_led.value(0)
        time.sleep(interval)


async def generate_test_audio(duration=1, frequency=440):
    """
    Generate test audio data (sine wave) for testing.
    
    Args:
        duration (float): Duration in seconds (limited to avoid memory issues)
        frequency (int): Frequency in Hz
        
    Returns:
        bytes: Audio data as bytes
    """
    # Force garbage collection before allocation
    gc.collect()
    
    # Limit duration to prevent excessive memory allocation
    duration = min(duration, 1.0)  # Max 1 second at a time
    
    # Calculate parameters
    sample_rate = AUDIO_SAMPLE_RATE
    # Limit number of samples to reduce memory usage
    num_samples = min(int(duration * sample_rate), sample_rate)

    # Create a smaller buffer for chunk generation
    chunk_size = 256  # Small chunk to avoid large allocations
    buffer = bytearray(chunk_size * (2 if AUDIO_CHANNELS == 1 else 4))
    
    # Pre-compute some values to save on calculations
    amplitude = 32767 * 0.5  # 50% amplitude to avoid clipping
    angular_freq = 2 * math.pi * frequency
    
    # Generate in small chunks (returning a generator instead of full buffer)
    total_chunks = (num_samples + chunk_size - 1) // chunk_size
    
    for chunk_idx in range(total_chunks):
        # Calculate start sample for this chunk
        start_sample = chunk_idx * chunk_size
        # Calculate actual samples in this chunk (might be less for last chunk)
        samples_in_chunk = min(chunk_size, num_samples - start_sample)
        
        # Generate chunk data
        for i in range(samples_in_chunk):
            t = (start_sample + i) / sample_rate
            value = int(amplitude * math.sin(angular_freq * t))
            
            if AUDIO_CHANNELS == 2:
                # Stereo: pack as two channels
                offset = i * 4
                struct.pack_into("<hh", buffer, offset, value, value)
            else:
                # Mono: pack as one channel
                offset = i * 2
                struct.pack_into("<h", buffer, offset, value)
        
        # Calculate actual size of this chunk's data
        bytes_used = samples_in_chunk * (2 if AUDIO_CHANNELS == 1 else 4)
        
        # Yield this chunk
        yield buffer[:bytes_used]
        
        # Force garbage collection between chunks
        gc.collect()


async def test_i2s_basic():
    """Test basic I2S functionality with a sine wave."""
    print("\n===== Testing basic I2S output =====")
    
    # Force garbage collection before starting
    gc.collect()
    
    # Initialize I2S driver
    i2s = I2SDriver(
        bck_pin=I2S_BCK_PIN,
        ws_pin=I2S_WS_PIN,
        sd_pin=I2S_SD_PIN
    )
    
    # Start I2S
    await i2s.start()
    
    print("Generating test audio...")
    
    # Create a short tone (0.5 seconds) at 440Hz
    try:
        # Generate and play in small chunks
        for chunk in await generate_test_audio(0.5, 440):
            buffer_full = await i2s.write(chunk)
            if buffer_full:
                # Wait for buffer to drain if full
                await asyncio.sleep_ms(10)
            # Small yield to avoid blocking
            await asyncio.sleep_ms(5)
        
        # Wait for playback to finish
        await asyncio.sleep(0.5)
        gc.collect()  # Force garbage collection
        
        # Try a different frequency (shorter duration)
        print("Playing test tone (880Hz)...")
        for chunk in await generate_test_audio(0.3, 880): 
            buffer_full = await i2s.write(chunk)
            if buffer_full:
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(5)
    except Exception as e:
        print(f"Error during I2S test: {e}")
    
    # Wait for playback to finish
    await asyncio.sleep(0.5)
    
    # Stop I2S
    await i2s.stop()
    
    print("I2S basic test completed")
    gc.collect()  # Force garbage collection
    return True


async def test_tone_sequence():
    """Test a sequence of tones to verify I2S output."""
    print("\n===== Testing tone sequence =====")
    
    # Force garbage collection before starting
    gc.collect()
    
    # Initialize I2S driver with smaller buffer
    i2s = I2SDriver(
        bck_pin=I2S_BCK_PIN,
        ws_pin=I2S_WS_PIN,
        sd_pin=I2S_SD_PIN,
        buffer_size=1024  # Smaller buffer to reduce memory usage
    )
    
    # Start I2S
    await i2s.start()
    
    # Define a sequence of notes (frequency in Hz, duration in seconds)
    # Use shorter durations to reduce memory usage
    notes = [
        (262, 0.2),  # C4
        (294, 0.2),  # D4
        (330, 0.2),  # E4
        (349, 0.2),  # F4
        (392, 0.2),  # G4
        (440, 0.2),  # A4
        (494, 0.2),  # B4
        (523, 0.3),  # C5
    ]
    
    # Play the sequence
    for frequency, duration in notes:
        print(f"Playing note: {frequency}Hz")
        try:
            # Generate and play in small chunks
            for chunk in await generate_test_audio(duration, frequency):
                buffer_full = await i2s.write(chunk)
                if buffer_full:
                    # Wait for buffer to drain if full
                    await asyncio.sleep_ms(10)
                # Small yield to avoid blocking
                await asyncio.sleep_ms(5)
            
            # Small gap between notes
            await asyncio.sleep_ms(50)
            
            # Force garbage collection between notes
            gc.collect()
        except Exception as e:
            print(f"Error playing note {frequency}Hz: {e}")
    
    # Stop I2S
    await i2s.stop()
    
    print("Tone sequence test completed")
    gc.collect()  # Force garbage collection
    return True


def run_test(test_function):
    """Run a test function in the asyncio event loop."""
    loop = asyncio.get_event_loop()
    
    print(f"Starting test: {test_function.__name__}")
    blink_led(times=2, interval=0.1)
    
    # Force garbage collection before test
    gc.collect()
    
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
    
    # Force garbage collection after test
    gc.collect()


def run_all_tests():
    """Run all tests in sequence."""
    print("\n===== Running all tests =====")
    
    try:
        # Force garbage collection before tests
        gc.collect()
        
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
        # Final garbage collection
        gc.collect()


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
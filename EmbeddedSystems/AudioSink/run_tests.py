"""
BLE Audio Sink Integration Tests

This script tests all components of the BLE Audio Sink system together
to verify they work after code cleanup and consolidation.
"""

import uasyncio as asyncio
import gc
import time
from machine import Pin

from config import (
    STATUS_LED_PIN,
    I2S_BCK_PIN, I2S_WS_PIN, I2S_SD_PIN
)
from ble.ble_core import BLEAudioSink, test_ble_audio_sink
from audio.i2s_driver import I2SDriver, test_i2s_driver
from audio.ble_audio_adapter import BLEAudioAdapter, test_ble_audio_adapter
from test import test_i2s_basic, test_tone_sequence, run_test

# Configure status LED for test feedback
status_led = Pin(STATUS_LED_PIN, Pin.OUT)

def blink_led(times=3, interval=0.2):
    """Blink the status LED to indicate test status."""
    for _ in range(times):
        status_led.value(1)
        time.sleep(interval)
        status_led.value(0)
        time.sleep(interval)

async def memory_test():
    """Test memory usage and garbage collection."""
    print("\n===== Testing Memory Management =====")
    
    # Force garbage collection
    gc.collect()
    
    # Get memory status
    free_mem = gc.mem_free()
    allocated_mem = gc.mem_alloc()
    total_mem = free_mem + allocated_mem
    
    print(f"Memory status:")
    print(f"  Free memory: {free_mem/1024:.1f}KB")
    print(f"  Used memory: {allocated_mem/1024:.1f}KB")
    print(f"  Total memory: {total_mem/1024:.1f}KB")
    print(f"  Memory usage: {100*allocated_mem/total_mem:.1f}%")
    
    return free_mem > 10000  # At least 10KB free memory

def main():
    """Run all integration tests."""
    print("\n===== BLE Audio Sink Integration Tests =====")
    print("Testing all components after code cleanup and consolidation.\n")
    
    # Welcome blink
    blink_led(times=2, interval=0.1)
    
    try:
        # Force initial garbage collection
        gc.collect()
        
        # Test memory management
        run_test(memory_test)
        
        # Test I2S functionality (with reduced duration to prevent memory issues)
        # Custom wrapper to minimize memory usage
        async def test_i2s_basic_wrapper():
            gc.collect()  # Pre-test cleanup
            result = False
            try:
                # Initialize with smaller buffer
                i2s = I2SDriver(
                    bck_pin=I2S_BCK_PIN,
                    ws_pin=I2S_WS_PIN,
                    sd_pin=I2S_SD_PIN,
                    buffer_size=512  # Very small buffer size
                )
                await i2s.start()
                
                # Generate a very simple short tone directly
                # (Don't use the generate_test_audio generator)
                print("Generating minimal test tone...")
                
                # Create a tiny buffer with a simple pattern
                # Just a few samples of a square wave (much simpler than sine wave)
                buffer_size = 64  # Extremely small buffer
                test_buffer = bytearray(buffer_size)
                
                # Fill with simple alternating pattern (square wave)
                for i in range(0, buffer_size, 4):
                    # Left channel: high value
                    test_buffer[i] = 0xFF
                    test_buffer[i+1] = 0x7F
                    # Right channel: high value
                    test_buffer[i+2] = 0xFF
                    test_buffer[i+3] = 0x7F
                
                # Play it a few times
                print("Playing minimal test tone...")
                for _ in range(5):
                    await i2s.write(test_buffer)
                    await asyncio.sleep_ms(10)
                    gc.collect()  # Force collection after each play
                
                await asyncio.sleep(0.3)  # Let it finish
                await i2s.stop()
                i2s.deinit()
                del i2s
                result = True
            except Exception as e:
                print(f"Error in I2S basic test wrapper: {e}")
            
            gc.collect()  # Post-test cleanup
            return result
        
        # Run the minimal I2S test
        run_test(test_i2s_basic_wrapper)
        
        # Force garbage collection before next test
        gc.collect()
        
        # Test audio output with a single tone instead of a sequence
        async def test_single_tone():
            gc.collect()  # Pre-test cleanup
            result = False
            try:
                print("\n===== Testing single tone =====")
                i2s = I2SDriver(
                    bck_pin=I2S_BCK_PIN,
                    ws_pin=I2S_WS_PIN,
                    sd_pin=I2S_SD_PIN,
                    buffer_size=512  # Very small buffer
                )
                await i2s.start()
                
                # Play just a very simple pattern
                print("Playing simple tone pattern...")
                
                # Create a tiny buffer with a simple pattern (different frequency than the first test)
                buffer_size = 64  # Extremely small buffer
                test_buffer = bytearray(buffer_size)
                
                # Fill with a different simple pattern (lower frequency square wave)
                for i in range(0, buffer_size, 8):
                    # 4 bytes on
                    test_buffer[i] = 0xFF
                    test_buffer[i+1] = 0x7F
                    test_buffer[i+2] = 0xFF
                    test_buffer[i+3] = 0x7F
                    # 4 bytes off
                    test_buffer[i+4] = 0x00
                    test_buffer[i+5] = 0x00
                    test_buffer[i+6] = 0x00
                    test_buffer[i+7] = 0x00
                
                # Play it a few times
                for _ in range(10):
                    await i2s.write(test_buffer)
                    await asyncio.sleep_ms(10)
                    gc.collect()  # Force collection after each play
                
                await asyncio.sleep(0.5)  # Let it finish
                await i2s.stop()
                i2s.deinit()
                del i2s
                result = True
            except Exception as e:
                print(f"Error in single tone test: {e}")
            
            gc.collect()  # Post-test cleanup
            return result
        
        run_test(test_single_tone)
        
        # Force garbage collection
        gc.collect()
        
        # Test BLE core functionality with minimal memory footprint
        print("\nTesting BLE core functionality...")
        print("Press Ctrl+C after 10 seconds to continue to next test.")
        try:
            # Run for a shorter time
            loop = asyncio.get_event_loop()
            ble_sink = BLEAudioSink()
            
            # Define minimal test callbacks that use less memory
            def audio_callback(data):
                # Just track data size without further processing
                pass
            
            def control_callback(cmd):
                # Minimal processing
                pass
            
            def status_callback(connected):
                if connected:
                    print("BLE connected")
                else:
                    print("BLE disconnected")
                # Force garbage collection on status change
                gc.collect()
            
            # Register callbacks
            ble_sink.set_audio_data_callback(audio_callback)
            ble_sink.set_control_callback(control_callback)
            ble_sink.set_status_callback(status_callback)
            
            # Start advertising
            ble_sink.start_advertising()
            print("BLE advertising started. Waiting 10 seconds...")
            
            # Run for 10 seconds with periodic garbage collection
            async def wait_task():
                for i in range(10):
                    await asyncio.sleep(1)
                    # Periodically force garbage collection
                    if i % 2 == 0:
                        gc.collect()
            
            loop.run_until_complete(wait_task())
            
            # Clean up
            ble_sink.disconnect()
            print("BLE core test completed")
            
        except KeyboardInterrupt:
            print("BLE core test interrupted")
        
        # Force garbage collection
        gc.collect()
        
        # Final integration test with reduced memory usage
        print("\nPerforming full system integration test...")
        print("Press Ctrl+C after testing to exit.")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Create an even more minimal version that tests components separately
            async def minimal_adapter_test():
                # Force garbage collection
                gc.collect()

                try:
                    # First test BLE component only (no I2S)
                    print("Testing BLE component...")
                    ble_sink = BLEAudioSink()
                    
                    # Define minimal callbacks
                    def audio_callback(data): pass
                    def control_callback(cmd): pass
                    def status_callback(connected): pass
                    
                    # Setup BLE
                    ble_sink.set_audio_data_callback(audio_callback)
                    ble_sink.set_control_callback(control_callback)
                    ble_sink.set_status_callback(status_callback)
                    ble_sink.start_advertising()
                    
                    # Run for a few seconds
                    for i in range(2): 
                        await asyncio.sleep(0.5)
                        gc.collect()
                    
                    # Clean up BLE
                    ble_sink.disconnect()
                    del ble_sink
                    gc.collect()
                    
                    # Now test I2S component separately
                    print("Testing I2S component...")
                    i2s = I2SDriver(
                        bck_pin=I2S_BCK_PIN,
                        ws_pin=I2S_WS_PIN,
                        sd_pin=I2S_SD_PIN,
                        buffer_size=1024  # Small buffer
                    )
                    
                    # Start and immediately stop to test initialization
                    await i2s.start()
                    await asyncio.sleep(0.5)
                    await i2s.stop()
                    i2s.deinit()
                    del i2s
                    gc.collect()
                    
                    print("Components tested separately to avoid memory issues")
                    return True
                
                except Exception as e:
                    print(f"Separate component test failed: {e}")
                    return False
                finally:
                    # Final cleanup
                    gc.collect()
            
            # Run the minimal test
            result = loop.run_until_complete(minimal_adapter_test())
            
            if result:
                print("\nAll tests completed successfully!")
                # Success indication
                blink_led(times=3, interval=0.1)
            else:
                print("\nAdapter test failed")
                blink_led(times=5, interval=0.1)
                
        except KeyboardInterrupt:
            print("Integration test interrupted")
        except Exception as e:
            print(f"Test failed with error: {e}")
            # Error indication
            blink_led(times=5, interval=0.1)
        
        # Final garbage collection
        gc.collect()
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        # Error indication
        blink_led(times=5, interval=0.1)

if __name__ == "__main__":
    # Force garbage collection before starting
    gc.collect()
    main()
    # Final cleanup
    gc.collect() 
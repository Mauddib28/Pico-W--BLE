"""
BLE Audio Sink Integration Tests

This script tests all components of the BLE Audio Sink system together
to verify they work after code cleanup and consolidation.
"""

import uasyncio as asyncio
import gc
import time
from machine import Pin

from config import STATUS_LED_PIN
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
        # Test memory management
        run_test(memory_test)
        
        # Test I2S functionality
        run_test(test_i2s_basic)
        
        # Test audio output with tone sequence
        run_test(test_tone_sequence)
        
        # Test BLE core functionality
        print("\nTesting BLE core functionality...")
        print("Press Ctrl+C after 10 seconds to continue to next test.")
        try:
            # Run for 10 seconds then move on
            loop = asyncio.get_event_loop()
            ble_sink = BLEAudioSink()
            
            # Define test callbacks
            def audio_callback(data):
                print(f"Received audio data: {len(data)} bytes")
            
            def control_callback(cmd):
                print(f"Received control command: {cmd}")
            
            def status_callback(connected):
                print(f"Connection status: {'Connected' if connected else 'Disconnected'}")
            
            # Register callbacks
            ble_sink.set_audio_data_callback(audio_callback)
            ble_sink.set_control_callback(control_callback)
            ble_sink.set_status_callback(status_callback)
            
            # Start advertising
            ble_sink.start_advertising()
            print("BLE advertising started. Waiting 10 seconds...")
            
            # Run for 10 seconds
            async def wait_task():
                await asyncio.sleep(10)
            
            loop.run_until_complete(wait_task())
            
            # Clean up
            ble_sink.disconnect()
            print("BLE core test completed")
            
        except KeyboardInterrupt:
            print("BLE core test interrupted")
        
        # Final integration test
        print("\nPerforming full system integration test...")
        print("Press Ctrl+C after testing to exit.")
        
        # Run the adapter for a limited time
        adapter = BLEAudioAdapter()
        
        async def run_adapter_test():
            # Start the adapter
            await adapter.start()
            
            # Run for 20 seconds
            for i in range(20):
                print(f"Adapter running... ({i+1}/20)")
                await asyncio.sleep(1)
            
            # Stop the adapter
            await adapter.stop()
        
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_adapter_test())
        except KeyboardInterrupt:
            print("Integration test interrupted")
            # Stop the adapter
            loop.run_until_complete(adapter.stop())
        
        print("\nAll tests completed successfully!")
        
        # Success indication
        blink_led(times=3, interval=0.1)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        # Error indication
        for _ in range(5):
            blink_led(times=2, interval=0.1)

if __name__ == "__main__":
    main() 
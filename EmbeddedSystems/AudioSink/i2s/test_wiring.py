#!/usr/bin/env python
# test_wiring.py - Test script for verifying I2S wiring connections
# 
# This script tests the wiring between the Raspberry Pi Pico WH and 
# the Adafruit I2S Stereo Decoder (UDA1334A)

import time
import machine
from i2s_config import init_i2s, start_i2s, play_test_tone, stop_i2s, set_i2s_volume

def run_wiring_test():
    """
    Run a comprehensive test of the I2S wiring connections.
    
    This function initializes the I2S interface, plays test tones at different
    volumes, and verifies the connections are working properly.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("Starting I2S wiring test...")
    print("1. Initializing I2S interface")
    
    try:
        # Initialize I2S interface
        i2s = init_i2s()
        if not i2s:
            print("❌ Failed to initialize I2S interface")
            return False
        
        print("✅ I2S interface initialized successfully")
        
        # Start I2S interface
        print("2. Starting I2S interface")
        start_i2s(i2s)
        print("✅ I2S interface started")
        
        # Set volume to 50%
        print("3. Setting volume to 50%")
        set_i2s_volume(50)
        print("✅ Volume set to 50%")
        
        # Play test tone
        print("4. Playing 1kHz test tone for 2 seconds")
        print("   You should hear a 1kHz tone at medium volume")
        play_test_tone(i2s, frequency=1000, duration_ms=2000)
        time.sleep(0.5)
        
        # Set volume to 80%
        print("5. Setting volume to 80%")
        set_i2s_volume(80)
        print("✅ Volume set to 80%")
        
        # Play another test tone
        print("6. Playing 500Hz test tone for 2 seconds")
        print("   You should hear a 500Hz tone at higher volume")
        play_test_tone(i2s, frequency=500, duration_ms=2000)
        time.sleep(0.5)
        
        # Stop I2S
        print("7. Stopping I2S interface")
        stop_i2s(i2s)
        print("✅ I2S interface stopped")
        
        print("\nWiring test completed successfully!")
        print("If you heard both test tones clearly, your wiring is correct.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_wiring_test()
    if success:
        print("\n✅ All tests passed! Wiring connections verified.")
    else:
        print("\n❌ Tests failed. Please check your wiring connections.")
        print("Refer to README.wiring for proper connection instructions.") 
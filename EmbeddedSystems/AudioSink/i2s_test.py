"""
i2s_test.py - Test script for I2S wiring connections

This script tests the wiring between the Raspberry Pi Pico WH and the
Adafruit I2S Stereo Decoder (UDA1334A) by toggling the I2S pins
and providing visual feedback through the onboard LED.

Connections to verify:
- Pico WH GPIO 0 -> I2S Decoder BCLK (Bit Clock)
- Pico WH GPIO 1 -> I2S Decoder LRCLK (Word Select/Left-Right Clock)
- Pico WH GPIO 2 -> I2S Decoder DIN (Data In)
- Pico WH GPIO 3 -> I2S Decoder MUTE (Optional)
- Pico WH 3.3V -> I2S Decoder VIN
- Pico WH GND -> I2S Decoder GND
"""

import machine
import time
from micropython import const

# Import I2S configuration
from i2s.i2s_config import (
    I2S_BCLK_PIN, 
    I2S_LRCLK_PIN, 
    I2S_DATA_PIN, 
    I2S_MUTE_PIN,
    play_test_tone
)

# Onboard LED for visual feedback
LED_PIN = const(25)  # Pico WH onboard LED is on GPIO 25

def setup():
    """Initialize test pins and LED"""
    # Configure the onboard LED
    led = machine.Pin(LED_PIN, machine.Pin.OUT)
    
    # Configure I2S pins as outputs
    bclk = machine.Pin(I2S_BCLK_PIN, machine.Pin.OUT)
    lrclk = machine.Pin(I2S_LRCLK_PIN, machine.Pin.OUT)
    data = machine.Pin(I2S_DATA_PIN, machine.Pin.OUT)
    mute = machine.Pin(I2S_MUTE_PIN, machine.Pin.OUT)
    
    # Initialize all pins to low
    bclk.value(0)
    lrclk.value(0)
    data.value(0)
    mute.value(0)
    
    return led, bclk, lrclk, data, mute

def blink_led(led, times=3, delay=0.2):
    """Blink the LED to indicate test phases"""
    for _ in range(times):
        led.value(1)
        time.sleep(delay)
        led.value(0)
        time.sleep(delay)

def test_pins(led, bclk, lrclk, data, mute):
    """Test each I2S pin individually"""
    pins = [
        (bclk, "BCLK (GPIO {})".format(I2S_BCLK_PIN)),
        (lrclk, "LRCLK (GPIO {})".format(I2S_LRCLK_PIN)),
        (data, "DATA (GPIO {})".format(I2S_DATA_PIN)),
        (mute, "MUTE (GPIO {})".format(I2S_MUTE_PIN))
    ]
    
    # Test each pin with a visible pattern
    for pin, name in pins:
        print(f"Testing {name}...")
        
        # Blink the LED once to indicate which pin we're testing
        blink_led(led, 1)
        
        # Toggle the pin 5 times
        for i in range(5):
            pin.value(1)
            time.sleep(0.1)
            pin.value(0)
            time.sleep(0.1)
        
        # Short pause between pin tests
        time.sleep(0.5)
    
    print("Individual pin tests complete")

def run_full_test():
    """Run a full wiring test sequence"""
    print("\n=== I2S Wiring Test ===")
    print(f"BCLK: GPIO {I2S_BCLK_PIN}")
    print(f"LRCLK: GPIO {I2S_LRCLK_PIN}")
    print(f"DATA: GPIO {I2S_DATA_PIN}")
    print(f"MUTE: GPIO {I2S_MUTE_PIN}")
    print("========================\n")
    
    # Initialize pins and LED
    led, bclk, lrclk, data, mute = setup()
    
    # Initial LED indication that test is starting
    blink_led(led, 3)
    
    # Test each pin individually
    test_pins(led, bclk, lrclk, data, mute)
    
    # Run a sequence to test all pins together
    print("Testing all pins in sequence...")
    for i in range(10):
        # Create a binary pattern based on the iteration
        bclk.value((i & 1) > 0)
        lrclk.value((i & 2) > 0)
        data.value((i & 4) > 0)
        mute.value((i & 8) > 0)
        
        # Flash LED in sync
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
    
    # Reset all pins to low
    bclk.value(0)
    lrclk.value(0)
    data.value(0)
    mute.value(0)
    
    print("Sequence test complete")
    
    # Now try to play a test tone using the I2S interface
    print("\nAttempting to play test tone...")
    try:
        play_test_tone()
        print("Test tone completed")
    except Exception as e:
        print(f"Error playing test tone: {e}")
    
    # Final indication that test is complete
    blink_led(led, 5, 0.1)
    print("\nWiring test complete! If you didn't see any errors, the connections are likely correct.")
    print("To verify fully, check if you could hear the test tone (although it might not be audible).")
    print("For a more thorough test, try running the full audio test in main.py")

if __name__ == "__main__":
    run_full_test() 
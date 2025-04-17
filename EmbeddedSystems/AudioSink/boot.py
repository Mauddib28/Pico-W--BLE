"""
Boot script for Raspberry Pi Pico W BLE Audio Sink

This file runs on every boot and handles system initialization.
"""

import machine
import gc
import time
import network
from machine import Pin

# Initialize status LED
status_led = Pin(25, Pin.OUT)
status_led.value(1)  # Turn on during boot

# Show boot indicator
for _ in range(3):
    status_led.value(0)
    time.sleep(0.1)
    status_led.value(1)
    time.sleep(0.1)

# Set frequency to maximum for audio processing
machine.freq(250000000)  # 250 MHz

# Disable WiFi to save power (we only need BLE)
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
ap = network.WLAN(network.AP_IF)
ap.active(False)

# Free up memory
gc.collect()

# Show ready indicator
status_led.value(0)
time.sleep(0.5)
status_led.value(1)
time.sleep(0.5)
status_led.value(0)

# Print boot message
print("\n===== Raspberry Pi Pico W BLE Audio Sink =====")
print(f"CPU Frequency: {machine.freq()/1000000} MHz")
print(f"Free memory: {gc.mem_free()/1024:.1f} KB")
print("System initialized. Starting main application...") 
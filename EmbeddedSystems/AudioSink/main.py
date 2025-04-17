"""
BLE Audio Sink Main Application

This is the main entry point for the BLE Audio Sink application.
It initializes the BLE audio adapter and handles system events.
"""

import uasyncio as asyncio
import machine
import gc
from machine import Pin

from audio.ble_audio_adapter import BLEAudioAdapter
from config import STATUS_LED_PIN, DEBUG_MODE

# Configure status LED
status_led = Pin(STATUS_LED_PIN, Pin.OUT)


async def status_indicator():
    """
    Status indicator task to blink the LED to indicate system status.
    - Fast blinking (250ms): Advertising, waiting for connection
    - Slow blinking (1000ms): Connected but no audio data
    - Steady on: Connected and receiving audio data
    - Three quick blinks: Error condition
    """
    led_state = False
    blink_rate = 0.25  # Start with fast blinking (advertising)
    
    while True:
        # Check system state
        if hasattr(app, 'adapter') and app.adapter.ble_sink.is_connected():
            # Connected
            if app.adapter.stats["packets_received"] > 0 and (
                    app.adapter.ble_sink.get_ticks_ms() - app.adapter.stats["last_packet_time"] < 1000):
                # Receiving audio data - steady on
                status_led.value(1)
                led_state = True
                await asyncio.sleep(1)
            else:
                # Connected but no audio data - slow blinking
                blink_rate = 1.0
                led_state = not led_state
                status_led.value(led_state)
                await asyncio.sleep(blink_rate)
        else:
            # Advertising - fast blinking
            blink_rate = 0.25
            led_state = not led_state
            status_led.value(led_state)
            await asyncio.sleep(blink_rate)


async def memory_monitor():
    """Monitor memory usage and perform garbage collection when needed."""
    while True:
        # Perform garbage collection
        gc.collect()
        
        if DEBUG_MODE:
            free_mem = gc.mem_free()
            allocated_mem = gc.mem_alloc()
            total_mem = free_mem + allocated_mem
            print(f"Memory: {free_mem/1024:.1f}KB free, {allocated_mem/1024:.1f}KB used, "
                  f"{100*free_mem/total_mem:.1f}% free")
        
        await asyncio.sleep(10)


class BLEAudioSinkApp:
    """Main application class for BLE Audio Sink."""
    
    def __init__(self):
        """Initialize the application."""
        self.adapter = None
        self.running = False
    
    async def start(self):
        """Start the application."""
        print("Starting BLE Audio Sink application...")
        self.running = True
        
        # Initialize hardware
        self._init_hardware()
        
        # Create and start BLE Audio Adapter
        self.adapter = BLEAudioAdapter()
        await self.adapter.start()
        
        # Start background tasks
        asyncio.create_task(status_indicator())
        asyncio.create_task(memory_monitor())
        
        # Keep the application running
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the application."""
        print("Stopping BLE Audio Sink application...")
        self.running = False
        
        if self.adapter:
            await self.adapter.stop()
        
        # Turn off LED
        status_led.value(0)
    
    def _init_hardware(self):
        """Initialize hardware components."""
        # Set CPU frequency to maximize performance
        machine.freq(250000000)  # 250 MHz
        
        # Initialize status LED
        status_led.value(0)
        
        # Additional hardware initialization can go here
        
        # Collect garbage after initialization
        gc.collect()
        
        if DEBUG_MODE:
            print(f"CPU Frequency: {machine.freq()/1000000} MHz")
            print(f"Free memory: {gc.mem_free()/1024:.1f} KB")


# Global application instance
app = BLEAudioSinkApp()


def main():
    """Main entry point for the application."""
    try:
        # Run the application
        asyncio.run(app.start())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nApplication interrupted by user")
    except Exception as e:
        # Handle other exceptions
        print(f"Error: {e}")
        
        # Blink LED rapidly to indicate error
        for _ in range(10):
            status_led.value(1)
            machine.sleep_ms(100)
            status_led.value(0)
            machine.sleep_ms(100)
    finally:
        # Ensure proper cleanup
        try:
            asyncio.run(app.stop())
        except:
            pass


if __name__ == "__main__":
    main() 
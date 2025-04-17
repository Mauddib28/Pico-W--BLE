"""
BLE Audio Sink - Core Implementation

This module implements the core Bluetooth Low Energy (BLE) functionality 
for the audio sink application.
"""

import bluetooth
import struct
import uasyncio as asyncio
import time
from micropython import const
from machine import Pin

from config import (
    BLE_DEVICE_NAME, MANUFACTURER_NAME, MODEL_NUMBER, FIRMWARE_VERSION,
    STATUS_LED_PIN, BLE_AUDIO_PACKET_SIZE, 
    BLE_DEVICE_INFO_SERVICE_UUID, BLE_AUDIO_SERVICE_UUID, BLE_AUDIO_CONTROL_SERVICE_UUID,
    BLE_MANUFACTURER_NAME_CHAR_UUID, BLE_MODEL_NUMBER_CHAR_UUID, BLE_FIRMWARE_REVISION_CHAR_UUID,
    BLE_AUDIO_DATA_CHAR_UUID, BLE_AUDIO_CONTROL_CHAR_UUID, BLE_AUDIO_STATUS_CHAR_UUID,
    BLE_IRQ_CENTRAL_CONNECT, BLE_IRQ_CENTRAL_DISCONNECT, BLE_IRQ_GATTS_WRITE,
    ADV_INTERVAL_MS, 
    CMD_PLAY, CMD_PAUSE, CMD_STOP,
    STATUS_READY, STATUS_PLAYING, STATUS_PAUSED, STATUS_STOPPED, STATUS_ERROR
)

class BLEAudioSink:
    def __init__(self, device_name=BLE_DEVICE_NAME):
        """Initialize BLE Audio Sink"""
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq_handler)
        
        self._device_name = device_name
        self._reset_state()
        
        # Callbacks
        self._audio_callback = None
        self._control_callback = None
        self._status_callback = None
        
        # Initialize status LED if available
        self._status_led = Pin(STATUS_LED_PIN, Pin.OUT, value=0)  # Onboard LED on Pico W
        
        # Setup services and start advertising
        self._setup_services()
        self._start_advertising()
        
        print(f"BLE Audio Sink initialized as '{self._device_name}'")
        
    def _reset_state(self):
        """Reset internal state variables."""
        self._connected = False
        self._conn_handle = None
        self._audio_buffer = bytearray()
        self._current_status = STATUS_READY
        self._last_packet_time = 0
        
    def set_audio_data_callback(self, callback):
        """Set callback for audio data processing."""
        self._audio_callback = callback
        
    def set_control_callback(self, callback):
        """Set callback for control command processing."""
        self._control_callback = callback
        
    def set_status_callback(self, callback):
        """Set callback for status updates."""
        self._status_callback = callback
    
    def is_connected(self):
        """Return connection status."""
        return self._connected
    
    def get_status(self):
        """Return current status."""
        return self._current_status
    
    def get_ticks_ms(self):
        """Get current time in milliseconds."""
        return time.ticks_ms()
    
    def _setup_services(self):
        """Setup BLE services and characteristics."""
        # Define handles for services and characteristics
        self._handles = {}
        
        # Device Information Service
        dev_info_service = (
            bluetooth.UUID(BLE_DEVICE_INFO_SERVICE_UUID),
            (
                (bluetooth.UUID(BLE_MANUFACTURER_NAME_CHAR_UUID), bluetooth.FLAG_READ),
                (bluetooth.UUID(BLE_MODEL_NUMBER_CHAR_UUID), bluetooth.FLAG_READ),
                (bluetooth.UUID(BLE_FIRMWARE_REVISION_CHAR_UUID), bluetooth.FLAG_READ),
            ),
        )
        
        # Audio Service
        audio_service = (
            bluetooth.UUID(BLE_AUDIO_SERVICE_UUID),
            (
                (bluetooth.UUID(BLE_AUDIO_DATA_CHAR_UUID), bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE),
            ),
        )
        
        # Audio Control Service
        audio_control_service = (
            bluetooth.UUID(BLE_AUDIO_CONTROL_SERVICE_UUID),
            (
                (bluetooth.UUID(BLE_AUDIO_CONTROL_CHAR_UUID), bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
                (bluetooth.UUID(BLE_AUDIO_STATUS_CHAR_UUID), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
            ),
        )
        
        # Register services
        dev_info_handles = self._ble.gatts_register_services((dev_info_service,))
        audio_handles = self._ble.gatts_register_services((audio_service,))
        control_handles = self._ble.gatts_register_services((audio_control_service,))
        
        # Set static values for Device Information Service
        self._ble.gatts_write(dev_info_handles[0][0], MANUFACTURER_NAME.encode())
        self._ble.gatts_write(dev_info_handles[0][1], MODEL_NUMBER.encode())
        self._ble.gatts_write(dev_info_handles[0][2], FIRMWARE_VERSION.encode())
        
        # Store handles for characteristics that need to be accessed later
        self._handles['audio_data'] = audio_handles[0][0]
        self._handles['audio_control'] = control_handles[0][0]
        self._handles['audio_status'] = control_handles[0][1]
        
        # Initialize status characteristic
        self._update_status(STATUS_READY)
    
    def start_advertising(self):
        """Start BLE advertising."""
        self._start_advertising()
    
    def _start_advertising(self):
        """Start BLE advertising."""
        # Advertising payload
        payload = bytearray()
        
        # Add flags
        payload += struct.pack("BB", 2, 0x01)  # Length 2, AD Type 0x01 (Flags)
        payload += struct.pack("B", 0x06)      # LE General Discoverable, BR/EDR not supported
        
        # Add complete name
        name_bytes = self._device_name.encode()
        payload += struct.pack("BB", len(name_bytes) + 1, 0x09)  # Length, AD Type 0x09 (Complete Local Name)
        payload += name_bytes
        
        # Add service UUIDs (16-bit UUIDs)
        payload += struct.pack("BBHHH", 5, 0x03, 
                               BLE_DEVICE_INFO_SERVICE_UUID, 
                               BLE_AUDIO_SERVICE_UUID, 
                               BLE_AUDIO_CONTROL_SERVICE_UUID)
        
        # Start advertising
        self._ble.gap_advertise(ADV_INTERVAL_MS, payload)  # ADV_INTERVAL_MS * 625us
        print("BLE advertising started")
    
    def _stop_advertising(self):
        """Stop BLE advertising."""
        self._ble.gap_advertise(None)
        print("BLE advertising stopped")
    
    def disconnect(self):
        """Disconnect any connected device and stop advertising."""
        if self._connected:
            self._ble.gap_disconnect(self._conn_handle)
        else:
            self._stop_advertising()
    
    def _irq_handler(self, event, data):
        """Handle BLE IRQ events."""
        if event == BLE_IRQ_CENTRAL_CONNECT:
            # Central device connected
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
            self._connected = True
            self._status_led.value(1)  # Turn on LED
            print("BLE central connected")
            self._update_status(STATUS_READY)
            if self._status_callback:
                self._status_callback(True)
        
        elif event == BLE_IRQ_CENTRAL_DISCONNECT:
            # Central device disconnected
            conn_handle, addr_type, addr = data
            self._conn_handle = None
            self._connected = False
            self._reset_state()
            self._status_led.value(0)  # Turn off LED
            print("BLE central disconnected")
            # Restart advertising
            self._start_advertising()
            if self._status_callback:
                self._status_callback(False)
        
        elif event == BLE_IRQ_GATTS_WRITE:
            # Write to a characteristic
            conn_handle, attr_handle = data
            
            if attr_handle == self._handles['audio_data']:
                # Audio data received
                value = self._ble.gatts_read(attr_handle)
                self._last_packet_time = time.ticks_ms()
                if self._audio_callback:
                    self._audio_callback(value)
            
            elif attr_handle == self._handles['audio_control']:
                # Control command received
                value = self._ble.gatts_read(attr_handle)
                if value and self._control_callback:
                    self._control_callback(value)
                
                # Update status based on command (if no callback provided)
                if not self._control_callback and value:
                    cmd = value[0]
                    if cmd == CMD_PLAY:
                        self._update_status(STATUS_PLAYING)
                    elif cmd == CMD_PAUSE:
                        self._update_status(STATUS_PAUSED)
                    elif cmd == CMD_STOP:
                        self._update_status(STATUS_STOPPED)
    
    def _update_status(self, status):
        """Update the status characteristic."""
        self._current_status = status
        if self._connected and self._handles.get('audio_status'):
            self._ble.gatts_write(self._handles['audio_status'], bytes([status]))
            self._ble.gatts_notify(self._conn_handle, self._handles['audio_status'])
    
    def set_status(self, status):
        """Update the status from external components."""
        self._update_status(status)

# Helper function for testing
def test_ble_audio_sink():
    """Test BLE Audio Sink functionality."""
    print("Initializing BLE Audio Sink...")
    ble_sink = BLEAudioSink()
    
    # Define callbacks
    def audio_data_callback(data):
        print(f"Received audio data: {len(data)} bytes")
        print(f"First few bytes: {data[:min(10, len(data))]}")
    
    def control_callback(cmd):
        print(f"Received control command: {cmd}")
    
    def status_callback(connected):
        print(f"Connection status changed: {'Connected' if connected else 'Disconnected'}")
    
    # Register callbacks
    ble_sink.set_audio_data_callback(audio_data_callback)
    ble_sink.set_control_callback(control_callback)
    ble_sink.set_status_callback(status_callback)
    
    print("BLE Audio Sink test running. Press Ctrl+C to stop.")
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        print("Test terminated by user")
        ble_sink.disconnect()

if __name__ == "__main__":
    test_ble_audio_sink() 
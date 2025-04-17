"""
BLE Device Implementation for Audio Sink

This module implements the BLE functionality for the Audio Sink device,
including initialization, advertising, connection management, and data handling.
"""

import bluetooth
import struct
import time
from machine import Pin
from micropython import const
from ble_config import *
import binascii

# Global variables
_ble = None  # BLE instance
_conn_handle = None  # Connection handle
_ble_status = STATUS_OFF  # Current BLE status
_adv_active = False  # Flag to track if advertising is active
_audio_buffer = bytearray(AUDIO_MTU)  # Buffer for audio data
_audio_data_available = False  # Flag to indicate audio data available
_led = Pin("LED", Pin.OUT)  # LED for status indication

# Flags for event handling
_events = {
    "new_data": False,
    "connection_change": False,
    "command_received": False,
    "last_command": 0
}

# Define the BLE services and characteristics
class BLEAudioSink:
    def __init__(self):
        self._service = None
        self._control_char = None
        self._data_char = None
        self._name_char = None
        self._device_info_service = None
        
    def setup(self, ble):
        # Create Audio Service
        self._service = bluetooth.Service(AUDIO_SERVICE_UUID)
        
        # Audio Control Characteristic
        self._control_char = bluetooth.Characteristic(
            self._service, AUDIO_CONTROL_CHAR_UUID,
            properties=bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY,
            value=struct.pack('<B', CMD_STOP)
        )
        
        # Audio Data Characteristic
        self._data_char = bluetooth.Characteristic(
            self._service, AUDIO_DATA_CHAR_UUID,
            properties=bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
            value=bytearray(1)  # Initial empty value
        )
        
        # Device Name Characteristic
        self._name_char = bluetooth.Characteristic(
            self._service, DEVICE_NAME_CHAR_UUID,
            properties=bluetooth.FLAG_READ,
            value=DEVICE_NAME
        )
        
        # Device Information Service
        self._device_info_service = bluetooth.Service(DEVICE_INFO_SERVICE_UUID)
        
        # Register services
        ble.add_service(self._service)
        ble.add_service(self._device_info_service)
        
        # Set up callbacks
        self._control_char.on_write(self._on_control_write)
        self._data_char.on_write(self._on_data_write)
        
    def _on_control_write(self, value):
        global _events
        if len(value) >= 1:
            _events["command_received"] = True
            _events["last_command"] = value[0]
            print("Control command received:", value[0])
            
    def _on_data_write(self, value):
        global _audio_buffer, _audio_data_available, _events
        # Copy data to audio buffer
        if len(value) > 0:
            _audio_buffer = value
            _audio_data_available = True
            _events["new_data"] = True
        

# BLE event handler
def _ble_irq(event, data):
    global _conn_handle, _ble_status, _events, _adv_active
    
    if event == bluetooth.IRQ_CENTRAL_CONNECT:
        _conn_handle = data[0]
        _adv_active = False
        _ble_status = STATUS_CONNECTED
        _events["connection_change"] = True
        _led.value(1)  # Turn LED on when connected
        print("BLE Central connected")
        
    elif event == bluetooth.IRQ_CENTRAL_DISCONNECT:
        _conn_handle = None
        _ble_status = STATUS_READY
        _events["connection_change"] = True
        _led.value(0)  # Turn LED off when disconnected
        print("BLE Central disconnected")
        # Restart advertising
        start_advertising()
        
    elif event == bluetooth.IRQ_GATTS_WRITE:
        # Handle writes to characteristics here
        # This is handled by the characteristic callbacks
        pass

# Initialize BLE
def init_ble():
    global _ble, _ble_status, _audio_device
    
    try:
        # Initialize BLE
        _ble = bluetooth.BLE()
        _ble.active(True)
        _ble.irq(_ble_irq)
        
        # Create and configure the Audio Sink device
        _audio_device = BLEAudioSink()
        _audio_device.setup(_ble)
        
        # Update status
        _ble_status = STATUS_READY
        print("BLE initialized successfully")
        return ERR_NONE
    except Exception as e:
        print("BLE initialization failed:", e)
        _ble_status = STATUS_ERROR
        return ERR_BLE_INIT_FAILED

# Start BLE advertising
def start_advertising():
    global _ble, _adv_active
    
    if _ble is None or _ble_status == STATUS_ERROR:
        return ERR_BLE_INIT_FAILED
    
    try:
        # Define advertising payload
        payload = bytearray()
        
        # Add device name
        name_bytes = DEVICE_NAME.encode()
        payload.extend(struct.pack('BB', len(name_bytes) + 1, 0x09))  # 0x09 = Complete Local Name
        payload.extend(name_bytes)
        
        # Add the service UUIDs
        payload.extend(struct.pack('BB', 3, 0x03))  # 0x03 = Complete List of 16-bit Service UUIDs
        payload.extend(struct.pack('<H', AUDIO_SERVICE_UUID))
        
        # Start advertising
        _ble.gap_advertise(ADV_INTERVAL_MS * 1000, adv_data=payload)
        _adv_active = True
        print("BLE advertising started")
        return ERR_NONE
    except Exception as e:
        print("Failed to start advertising:", e)
        return ERR_ADV_START_FAILED

# Stop BLE advertising
def stop_advertising():
    global _ble, _adv_active
    
    if _ble is None:
        return
    
    _ble.gap_advertise(None)  # Stop advertising
    _adv_active = False
    print("BLE advertising stopped")

# Check if device is connected
def is_connected():
    global _conn_handle
    return _conn_handle is not None

# Get audio data if available
def get_audio_data():
    global _audio_buffer, _audio_data_available, _events
    
    if _audio_data_available:
        _audio_data_available = False
        _events["new_data"] = False
        return _audio_buffer
    return None

# Get received command
def get_command():
    global _events
    
    if _events["command_received"]:
        _events["command_received"] = False
        return _events["last_command"]
    return None

# Check for new events
def has_new_events():
    global _events
    return _events["new_data"] or _events["connection_change"] or _events["command_received"]

# Update BLE status
def update_status(status):
    global _ble_status
    _ble_status = status

# Get current BLE status
def get_status():
    global _ble_status
    return _ble_status 
"""
ble_config.py - BLE Configuration and Constants

This module contains configuration settings and constants for the
BLE audio sink implementation.
"""

import bluetooth
from micropython import const

# BLE Service UUIDs (convert to MicroPython compatible format)
BLE_AUDIO_SERVICE_UUID = bluetooth.UUID("1234")  # Custom UUID for Audio Service
BLE_MEDIA_CONTROL_SERVICE_UUID = bluetooth.UUID("1235")  # Custom UUID for Media Control
BLE_VOLUME_CONTROL_SERVICE_UUID = bluetooth.UUID("1236")  # Custom UUID for Volume Control
BLE_STATUS_SERVICE_UUID = bluetooth.UUID("1237")  # Custom UUID for Status Service

# BLE Characteristic UUIDs
BLE_AUDIO_DATA_CHAR_UUID = bluetooth.UUID("1238")  # Audio data characteristic
BLE_MEDIA_CONTROL_CHAR_UUID = bluetooth.UUID("1239")  # Media control characteristic
BLE_VOLUME_CHAR_UUID = bluetooth.UUID("123A")  # Volume control characteristic
BLE_STATUS_CHAR_UUID = bluetooth.UUID("123B")  # Status characteristic

# L2CAP parameters
BLE_L2CAP_PSM = const(0x25)   # L2CAP PSM value
BLE_L2CAP_RX_MTU = const(512)  # Maximum receive MTU
BLE_L2CAP_TX_MTU = const(512)  # Maximum transmit MTU

# Media control commands
MEDIA_CMD_PLAY = const(0x01)
MEDIA_CMD_PAUSE = const(0x02)
MEDIA_CMD_RESUME = const(0x03)
MEDIA_CMD_STOP = const(0x04)

# Status codes
STATUS_IDLE = const(0x00)
STATUS_PLAYING = const(0x01)
STATUS_PAUSED = const(0x02)
STATUS_STOPPED = const(0x03)
STATUS_ERROR = const(0xFF)

# Function declarations - will be implemented in separate files
def init_ble():
    """Initialize BLE stack"""
    pass

def setup_ble_services():
    """Set up BLE services and characteristics"""
    pass

def advertise_ble_services():
    """Start advertising BLE services"""
    pass

def handle_ble_connections():
    """Handle BLE connection events"""
    pass

def setup_l2cap_channel():
    """Set up L2CAP channel for audio data"""
    pass

def handle_l2cap_data(data, length):
    """Handle incoming L2CAP data"""
    pass

def send_status_update(status):
    """Send status update to connected clients"""
    pass

def handle_media_control(command):
    """Handle media control commands"""
    pass

def handle_volume_control(volume):
    """Handle volume control commands"""
    pass 
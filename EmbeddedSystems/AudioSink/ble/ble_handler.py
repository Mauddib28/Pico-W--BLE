"""
BLE Audio Sink - Event Handler

This module contains the event handler for BLE events and manages the BLE state machine.
"""
import bluetooth
from micropython import const
from machine import Pin
import ubinascii

from .ble_config import *

# Status LED pin - used to indicate connection status
status_led = Pin("LED", Pin.OUT)

# Internal state variables
_ble = None  # BLE instance
_connection = None  # Current connection (if connected)
_connected = False  # Connection state
_services = {}  # Dictionary of services
_characteristics = {}  # Dictionary of characteristics
_current_status = STATUS_OFF  # Current status of the device
_event_flags = EVT_NONE  # Event flags
_received_data = None  # Last received data
_received_command = None  # Last received command

# Callback definitions
_data_callback = None  # Callback for audio data
_command_callback = None  # Callback for control commands
_status_callback = None  # Callback for status changes

# BLE event handler
def _irq_handler(event, data):
    """
    BLE event handler - processes all BLE events and updates state accordingly
    """
    global _connection, _connected, _event_flags, _received_data, _received_command, _current_status
    
    if event == bluetooth.IRQ_CENTRAL_CONNECT:
        # A central (like a smartphone) has connected
        _connection = data[0]
        _connected = True
        _event_flags |= EVT_CONNECTED
        _update_status(STATUS_CONNECTED)
        status_led.on()  # Turn on LED when connected
        print("BLE: Connected to", ubinascii.hexlify(_connection).decode())
    
    elif event == bluetooth.IRQ_CENTRAL_DISCONNECT:
        # Central has disconnected
        _connection = None
        _connected = False
        _event_flags |= EVT_DISCONNECTED
        _update_status(STATUS_READY)
        status_led.off()  # Turn off LED when disconnected
        print("BLE: Disconnected")
        
        # Start advertising again
        start_advertising()
    
    elif event == bluetooth.IRQ_GATTS_WRITE:
        # Client has written to a characteristic
        conn_handle, value_handle = data
        
        # Identify which characteristic was written to
        if value_handle == _characteristics[CHAR_AUDIO_DATA]:
            # Audio data received
            _received_data = _ble.gatts_read(value_handle)
            _event_flags |= EVT_NEW_DATA
            
            # Call the data callback if registered
            if _data_callback:
                _data_callback(_received_data)
        
        elif value_handle == _characteristics[CHAR_AUDIO_CONTROL]:
            # Command received
            cmd_data = _ble.gatts_read(value_handle)
            if len(cmd_data) > 0:
                _received_command = cmd_data[0]  # First byte is command code
                _event_flags |= EVT_NEW_COMMAND
                
                # Process the command
                _process_command(_received_command, cmd_data[1:] if len(cmd_data) > 1 else None)
    
    elif event == bluetooth.IRQ_MTU_EXCHANGED:
        # MTU was negotiated (important for audio streaming)
        conn_handle, mtu = data
        print(f"BLE: MTU exchanged - {mtu} bytes")

def init(data_cb=None, command_cb=None, status_cb=None):
    """
    Initialize the BLE subsystem
    
    Args:
        data_cb: Callback function for audio data reception
        command_cb: Callback function for command reception
        status_cb: Callback function for status changes
    
    Returns:
        bool: True if initialized successfully, False otherwise
    """
    global _ble, _data_callback, _command_callback, _status_callback, _current_status
    
    # Store callbacks
    _data_callback = data_cb
    _command_callback = command_cb
    _status_callback = status_cb
    
    try:
        # Initialize BLE
        _ble = bluetooth.BLE()
        _ble.active(True)
        _ble.irq(_irq_handler)
        
        # Register services
        _register_services()
        
        _update_status(STATUS_READY)
        return True
    except Exception as e:
        print(f"BLE initialization error: {e}")
        _update_status(STATUS_ERROR)
        return False

def _register_services():
    """Register all the BLE services and characteristics"""
    global _services, _characteristics
    
    # Audio Service
    _services[SVC_AUDIO] = _ble.gatts_register_services([(
        SVC_AUDIO, 
        [
            (CHAR_AUDIO_DATA, bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
            (CHAR_STATUS, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
        ]
    )])
    
    # Control Service
    _services[SVC_CONTROL] = _ble.gatts_register_services([(
        SVC_CONTROL,
        [
            (CHAR_AUDIO_CONTROL, bluetooth.FLAG_WRITE)
        ]
    )])
    
    # Device Information Service
    _services[SVC_DEVICE_INFO] = _ble.gatts_register_services([(
        SVC_DEVICE_INFO,
        [
            (CHAR_MFR_NAME, bluetooth.FLAG_READ),
            (CHAR_MODEL_NUM, bluetooth.FLAG_READ),
            (CHAR_FIRMWARE_REV, bluetooth.FLAG_READ)
        ]
    )])
    
    # Store the characteristic handles for easy access
    _characteristics[CHAR_AUDIO_DATA] = _services[SVC_AUDIO][0][1]
    _characteristics[CHAR_STATUS] = _services[SVC_AUDIO][1][1]
    _characteristics[CHAR_AUDIO_CONTROL] = _services[SVC_CONTROL][0][1]
    _characteristics[CHAR_MFR_NAME] = _services[SVC_DEVICE_INFO][0][1]
    _characteristics[CHAR_MODEL_NUM] = _services[SVC_DEVICE_INFO][1][1]
    _characteristics[CHAR_FIRMWARE_REV] = _services[SVC_DEVICE_INFO][2][1]
    
    # Initialize values for the characteristics
    _ble.gatts_write(_characteristics[CHAR_STATUS], bytes([_current_status]))
    _ble.gatts_write(_characteristics[CHAR_MFR_NAME], MANUFACTURER_NAME.encode())
    _ble.gatts_write(_characteristics[CHAR_MODEL_NUM], "Pico W".encode())
    _ble.gatts_write(_characteristics[CHAR_FIRMWARE_REV], FIRMWARE_VERSION.encode())

def start_advertising():
    """Start BLE advertising"""
    # Advertising payload: device name and complete list of services
    payload = bytearray()
    
    # Add device name
    name_bytes = DEVICE_NAME.encode()
    payload.extend(struct.pack("BB", len(name_bytes) + 1, 0x09) + name_bytes)  # 0x09 = Complete Local Name
    
    # Add service UUIDs (complete list of 128-bit UUIDs)
    services = bytearray()
    services.extend(SVC_AUDIO)
    services.extend(SVC_CONTROL)
    payload.extend(struct.pack("BB", len(services) + 1, 0x07) + services)  # 0x07 = Complete List of 128-bit Service UUIDs
    
    # Start advertising
    try:
        _ble.gap_advertise(ADV_INTERVAL_MS * 1000, payload)
        return True
    except Exception as e:
        print(f"BLE advertising error: {e}")
        _update_status(STATUS_ERROR)
        return False

def stop_advertising():
    """Stop BLE advertising"""
    _ble.gap_advertise(None)

def _process_command(cmd, data=None):
    """
    Process a received command
    
    Args:
        cmd: Command code
        data: Optional command data
    """
    global _current_status
    
    if cmd == CMD_PLAY:
        _update_status(STATUS_PLAYING)
    elif cmd == CMD_PAUSE:
        _update_status(STATUS_PAUSED)
    elif cmd == CMD_STOP:
        _update_status(STATUS_CONNECTED)
    elif cmd == CMD_VOLUME:
        # Volume adjustment (if data is provided)
        if data and len(data) > 0:
            volume_level = data[0]
            print(f"BLE: Volume set to {volume_level}")
    
    # Call the command callback if registered
    if _command_callback:
        _command_callback(cmd, data)

def _update_status(status):
    """
    Update the device status and notify the client if connected
    
    Args:
        status: New status code
    """
    global _current_status, _event_flags
    
    if _current_status != status:
        _current_status = status
        _event_flags |= EVT_STATUS_CHANGE
        
        # Update the status characteristic
        if _ble and CHAR_STATUS in _characteristics:
            _ble.gatts_write(_characteristics[CHAR_STATUS], bytes([status]))
            
            # Notify if connected
            if _connected:
                _ble.gatts_notify(_connection, _characteristics[CHAR_STATUS])
        
        # Call the status callback if registered
        if _status_callback:
            _status_callback(status)

def get_status():
    """Get the current status"""
    return _current_status

def is_connected():
    """Check if a device is connected"""
    return _connected

def get_events():
    """
    Get and clear event flags
    
    Returns:
        int: Event flags
    """
    global _event_flags
    events = _event_flags
    _event_flags = EVT_NONE
    return events

def get_received_data():
    """
    Get the last received audio data
    
    Returns:
        bytes: Audio data or None if no data available
    """
    global _received_data
    data = _received_data
    _received_data = None
    return data

def get_received_command():
    """
    Get the last received command
    
    Returns:
        tuple: (command code, command data) or None if no command available
    """
    global _received_command
    cmd = _received_command
    _received_command = None
    return cmd

# Module initialization
import struct  # Import here to avoid circular imports 
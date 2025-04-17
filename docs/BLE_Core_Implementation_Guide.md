# BLE Core Implementation Guide

This guide provides detailed steps for implementing the core Bluetooth Low Energy (BLE) functionality for the Raspberry Pi Pico W Audio Sink project.

## Overview

The BLE Core Implementation establishes the foundation for Bluetooth connectivity, allowing audio devices to discover and connect to our Pico W audio sink. This implementation handles device advertising, connection management, and defines the necessary services and characteristics for audio data transfer.

## Prerequisites

- Raspberry Pi Pico W with MicroPython firmware
- Understanding of BLE concepts (services, characteristics, advertising)
- MicroPython's `bluetooth` library

## Implementation Steps

### 3.1 Initialize BLE Module

**Objective**: Set up the BLE module with proper device identifier and configuration.

**Implementation Notes**:
- Import the `bluetooth` module from MicroPython
- Configure the BLE driver with a unique device name
- Initialize the Bluetooth module in BLE mode
- Set up event handlers for BLE operations

**Code Skeleton**:
```python
from machine import Pin
import bluetooth
from micropython import const

class BLEAudioSink:
    def __init__(self, name="BLE Audio Sink"):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._name = name
        self._ble.config(gap_name=self._name)
        self._ble.irq(self._irq_handler)
        
        # Status LED for visual feedback
        self._led = Pin("LED", Pin.OUT)
        self._connected = False
        
        print(f"BLE Audio Sink initialized as '{self._name}'")
```

### 3.2 Implement Device Advertising

**Objective**: Configure BLE advertising with proper device name and service UUIDs.

**Implementation Notes**:
- Define service UUIDs for advertising
- Create advertising payload with device name and service UUIDs
- Set appropriate advertising interval (balance between power and discoverability)
- Include response data for scan requests

**Code Skeleton**:
```python
def _start_advertising(self):
    # Define service UUIDs
    AUDIO_SERVICE_UUID = bluetooth.UUID("ABCD")  # Use standard UUID in actual implementation
    
    # Advertising payload
    payload = bytearray()
    # Add flags
    payload += struct.pack("BB", 2, 0x01)  # Length 2, AD Type 0x01 (Flags)
    payload += struct.pack("B", 0x06)      # LE General Discoverable, BR/EDR not supported
    
    # Add complete name
    name_bytes = self._name.encode()
    payload += struct.pack("BB", len(name_bytes) + 1, 0x09)  # Length, AD Type 0x09 (Complete Local Name)
    payload += name_bytes
    
    # Add service UUIDs
    payload += struct.pack("BB", 17, 0x07)  # Length 17, AD Type 0x07 (Complete List of 128-bit UUIDs)
    payload += AUDIO_SERVICE_UUID.to_bytes()
    
    # Start advertising
    self._ble.gap_advertise(100, payload)  # 100ms interval
    print("BLE advertising started")
```

### 3.3 Define Core BLE Services

**Objective**: Define essential BLE services for device identification and audio functionality.

**Implementation Notes**:
- Create Device Information Service (DIS) with manufacturer and model details
- Define custom Audio Service with characteristics for:
  - Audio Data Transfer
  - Audio Configuration
  - Status Notification
- Set appropriate permissions and properties for each characteristic

**Code Skeleton**:
```python
def _setup_services(self):
    # Define UUIDs
    DEVICE_INFO_UUID = bluetooth.UUID(0x180A)  # Device Information Service
    MANUFACTURER_UUID = bluetooth.UUID(0x2A29)  # Manufacturer Name
    MODEL_NUMBER_UUID = bluetooth.UUID(0x2A24)  # Model Number
    
    AUDIO_SERVICE_UUID = bluetooth.UUID("ABCD")  # Custom audio service
    AUDIO_DATA_UUID = bluetooth.UUID("ABCD1")    # Audio data characteristic
    AUDIO_CTRL_UUID = bluetooth.UUID("ABCD2")    # Audio control characteristic
    AUDIO_STATUS_UUID = bluetooth.UUID("ABCD3")  # Audio status characteristic
    
    # Device Information Service
    dis = self._ble.gatts_register_services([(
        DEVICE_INFO_UUID, 
        [
            (MANUFACTURER_UUID, bluetooth.FLAG_READ),
            (MODEL_NUMBER_UUID, bluetooth.FLAG_READ),
        ]
    )])
    
    # Write device information
    self._ble.gatts_write(dis[0], "Raspberry Pi Foundation".encode())
    self._ble.gatts_write(dis[1], "Pico W Audio Sink".encode())
    
    # Audio Service
    audio_service = self._ble.gatts_register_services([(
        AUDIO_SERVICE_UUID,
        [
            (AUDIO_DATA_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE),
            (AUDIO_CTRL_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
            (AUDIO_STATUS_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
        ]
    )])
    
    # Store handles for later use
    self._audio_data_handle = audio_service[0]
    self._audio_ctrl_handle = audio_service[1]
    self._audio_status_handle = audio_service[2]
    
    # Initialize status
    self._ble.gatts_write(self._audio_status_handle, b'\x00')  # 0 = Ready
```

### 3.4 Implement Connection Management

**Objective**: Handle BLE connection events and maintain connection state.

**Implementation Notes**:
- Implement callbacks for connection events
- Handle disconnection and reconnection scenarios
- Track and maintain connection state
- Provide visual feedback through LED indicators

**Code Skeleton**:
```python
def _handle_connect(self, conn_handle):
    self._conn_handle = conn_handle
    self._connected = True
    print(f"Device connected: handle = {conn_handle}")
    
    # Visual feedback
    self._led.on()
    
    # Set status as connected
    self._ble.gatts_write(self._audio_status_handle, b'\x01')  # 1 = Connected
    self._ble.gatts_notify(conn_handle, self._audio_status_handle)

def _handle_disconnect(self):
    if self._connected:
        print("Device disconnected")
        self._connected = False
        self._conn_handle = None
        
        # Visual feedback
        self._led.off()
        
        # Reset status
        self._ble.gatts_write(self._audio_status_handle, b'\x00')  # 0 = Ready
        
        # Restart advertising
        self._start_advertising()
```

### 3.5 Create BLE IRQ Handler

**Objective**: Implement interrupt request handler for BLE events.

**Implementation Notes**:
- Create a central event handler for all BLE interrupts
- Handle various event types:
  - Connection events
  - Disconnection events
  - Write events to characteristics
  - Notification subscription events
- Route events to appropriate handler methods

**Code Skeleton**:
```python
def _irq_handler(self, event, data):
    if event == bluetooth.IRQ_CENTRAL_CONNECT:
        # Central device connected
        conn_handle, _, _ = data
        self._handle_connect(conn_handle)
        
    elif event == bluetooth.IRQ_CENTRAL_DISCONNECT:
        # Central device disconnected
        conn_handle, _, _ = data
        self._handle_disconnect()
        
    elif event == bluetooth.IRQ_GATTS_WRITE:
        # A client has written to a characteristic or descriptor
        conn_handle, value_handle = data
        
        if value_handle == self._audio_data_handle:
            # Handle audio data write
            data = self._ble.gatts_read(value_handle)
            if self._audio_callback:
                self._audio_callback(data)
                
        elif value_handle == self._audio_ctrl_handle:
            # Handle control command
            data = self._ble.gatts_read(value_handle)
            if self._control_callback:
                self._control_callback(data)
```

### 3.6 Test BLE Discoverability

**Objective**: Test that the device is properly discoverable with correct advertising data.

**Implementation Notes**:
- Create a test script to initialize the BLE Audio Sink
- Set up simple callbacks for testing
- Verify the following with a BLE scanner app:
  - Device is visible with correct name
  - Advertised services are present
  - Can establish connection successfully

**Test Code**:
```python
def test_ble_audio_sink():
    from machine import Pin
    import uasyncio as asyncio
    
    def audio_callback(data):
        print(f"Received audio data: {len(data)} bytes")
    
    def control_callback(cmd):
        print(f"Received control command: {cmd}")
    
    # Initialize BLE Audio Sink
    ble_sink = BLEAudioSink("BLE Audio Sink")
    ble_sink.set_audio_callback(audio_callback)
    ble_sink.set_control_callback(control_callback)
    
    # Start advertising
    ble_sink.start()
    
    # Create event loop to keep program running
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == "__main__":
    test_ble_audio_sink()
```

## Next Steps

After successfully implementing the BLE Core functionality:

1. Test the implementation with a BLE scanner app
2. Proceed to implementing audio data handling 
3. Connect with audio source devices for testing
4. Integrate with the I2S audio output module

## Troubleshooting

- **Device not discoverable**: Check advertising payload format and ensure BLE is active
- **Connection failures**: Verify the service UUIDs are correctly configured
- **No data reception**: Check characteristic permissions and IRQ handler implementation 
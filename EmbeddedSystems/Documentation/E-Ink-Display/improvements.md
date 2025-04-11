# Potential Improvements for Pico W BLE E-Ink Display

This document outlines potential improvements that could be made to the existing BLE E-Ink Display implementation.

## Feature Enhancements

### 1. Enhanced Display Text Formatting

**Description**: Add support for multi-line text formatting and text positioning.

**Implementation Steps**:
- Extend the display_text method to handle line breaks
- Add parameters for X/Y positioning
- Create a new characteristic for font/style settings
- Implement a simple text formatting protocol

**Code Changes**:
```python
def display_text(self, text, x=0, y=0, font_size=1):
    # Clear display area
    self.fill_rect(x, y, self.width - x, 20 * font_size, 0xFF)
    
    # Handle multi-line text
    lines = text.split('\n')
    for i, line in enumerate(lines):
        self.text(line, x, y + (i * 10 * font_size), 0x00)
    
    self.display(self.buffer)
```

### 2. Image Support

**Description**: Add capability to display simple monochrome images.

**Implementation Steps**:
- Create a new characteristic for image data transfer
- Implement binary data handling for images
- Add support for common image formats (BMP, PNG)
- Create a buffer handling system for multi-packet transfers

**Code Changes**:
```python
def display_image(self, image_data, x=0, y=0):
    # Convert image data to display format
    image = framebuf.FrameBuffer(bytearray(image_data), 64, 64, framebuf.MONO_HLSB)
    
    # Copy to display buffer
    self.blit(image, x, y)
    
    # Update display
    self.display(self.buffer)
```

### 3. Battery Status Monitoring

**Description**: Add battery level reporting via a new characteristic.

**Implementation Steps**:
- Add ADC reading from battery pin
- Create a new Battery Service with Battery Level characteristic
- Implement periodic battery level updates
- Add low battery warning display

**Code Changes**:
```python
def _init_battery_service(self):
    # Define Battery Service
    _BATT_UUID = bluetooth.UUID(0x180F)  # Standard Battery Service
    _BATT_LEVEL = (bluetooth.UUID(0x2A19), _FLAG_READ | _FLAG_NOTIFY)
    _BATT_SERVICE = (_BATT_UUID, (_BATT_LEVEL,))
    
    # Register battery service
    ((self._handle_batt_level,),) = self._ble.gatts_register_services((_BATT_SERVICE,))
    
    # Initialize battery level
    self._update_battery_level()

def _update_battery_level(self):
    # Read battery voltage from ADC
    adc = ADC(Pin(29))  # Assuming battery monitoring on GPIO 29
    voltage = adc.read_u16() * 3.3 / 65535
    
    # Convert to percentage (assuming 3.0V min, 4.2V max)
    percentage = int(((voltage - 3.0) / 1.2) * 100)
    percentage = max(0, min(100, percentage))  # Clamp to 0-100
    
    # Update characteristic
    self._ble.gatts_write(self._handle_batt_level, bytes([percentage]))
```

### 4. Power Management

**Description**: Improve power efficiency with sleep modes.

**Implementation Steps**:
- Implement deep sleep support between updates
- Add timer-based wake-up system
- Create a characteristic to control power modes
- Add display sleep/wake commands

**Code Changes**:
```python
def _handle_command(self, cmd):
    """Handle display commands"""
    if cmd == "clear":
        self._eink.clear()
        self._display_text = ""
        self._update_status("Display cleared")
    elif cmd == "refresh":
        self._eink.display_frame()
        self._update_status("Display refreshed")
    elif cmd == "sleep":
        self._enter_low_power_mode()
        self._update_status("Entering low power mode")
    elif cmd == "wake":
        self._exit_low_power_mode()
        self._update_status("Exiting low power mode")
    else:
        self._update_status(f"Unknown command: {cmd}")
        
def _enter_low_power_mode(self):
    # Sleep the display
    self._eink.sleep()
    
    # Reduce BLE advertising interval
    self._ble.gap_advertise(2000000)  # 2 second interval
    
    # TODO: Enter MCU low power mode
```

### 5. Robust Error Handling

**Description**: Add comprehensive error handling and reporting.

**Implementation Steps**:
- Create error status notifications
- Implement error recovery procedures
- Add error logging
- Create a diagnostic characteristic

**Code Changes**:
```python
def _report_error(self, error_code, message):
    """Report errors to connected clients"""
    error = {
        "code": error_code,
        "message": message
    }
    error_json = json.dumps(error)
    
    self._update_status(f"Error: {error_code}")
    
    # Notify connected clients if any
    if self._handle_error_notify and self._connections:
        self._ble.gatts_notify(0, self._handle_error_notify, error_json.encode())
```

### 6. Security Features

**Description**: Add secure pairing and encryption.

**Implementation Steps**:
- Implement BLE security features
- Add pairing request handling
- Implement encryption for sensitive data
- Set up authorization for critical characteristics

**Code Changes**:
```python
def _init_security(self):
    # Set security level to require encryption
    self._ble.config(gap_name=self._name, security=SECURITY_MODE_ENC_WITH_MITM)
    
    # Enable pairing
    self._ble.config(bond=True)
```

### 7. Notification Improvements

**Description**: Implement proper notification handling for status changes.

**Implementation Steps**:
- Set up notification system for all status changes
- Add notification subscription tracking
- Optimize notification frequency
- Add batch notifications for efficiency

**Code Changes**:
```python
def _update_status(self, status):
    if dbg:
        print(f"[*] Status: {status}")
    self._ble.gatts_write(self._handle_read_status, status.encode())
    
    # Notify connected clients if they have subscribed
    if self._status_subscriptions:
        for conn_handle in self._status_subscriptions:
            self._ble.gatts_notify(conn_handle, self._handle_read_status, status.encode())
```

### 8. Command Set Expansion

**Description**: Expand the command set beyond just "clear" and "refresh".

**Implementation Steps**:
- Add more commands like contrast adjustment, rotation
- Implement partial updates for efficiency
- Add drawing commands for lines, rectangles, etc.
- Create a simple command protocol

**Code Changes**:
```python
def _handle_command(self, cmd_string):
    """Handle extended command set"""
    try:
        # Parse command and arguments
        parts = cmd_string.split(':')
        cmd = parts[0]
        args = parts[1].split(',') if len(parts) > 1 else []
        
        if cmd == "clear":
            self._eink.clear()
            self._display_text = ""
            self._update_status("Display cleared")
        elif cmd == "refresh":
            self._eink.display_frame()
            self._update_status("Display refreshed")
        elif cmd == "rotate":
            rotation = int(args[0]) if args else 0
            self._eink.rotation = rotation
            self._update_status(f"Display rotated: {rotation}")
        elif cmd == "contrast":
            contrast = int(args[0]) if args else 0
            self._eink.contrast(contrast)
            self._update_status(f"Contrast set: {contrast}")
        elif cmd == "rect":
            if len(args) >= 4:
                x, y, w, h = map(int, args[0:4])
                fill = int(args[4]) if len(args) > 4 else 0
                if fill:
                    self._eink.fill_rect(x, y, w, h, 0x00)
                else:
                    self._eink.rect(x, y, w, h, 0x00)
                self._eink.display(self._eink.buffer)
                self._update_status("Rectangle drawn")
        else:
            self._update_status(f"Unknown command: {cmd}")
    except Exception as e:
        self._update_status(f"Command error: {str(e)}")
```

## Implementation Priority

Based on utility and complexity, here's a suggested implementation order:

1. Text Formatting - Highest immediate value
2. Command Set Expansion - Builds on existing functionality
3. Notification Improvements - Better client experience
4. Power Management - Important for battery-powered applications
5. Battery Status Monitoring - Useful feedback for users
6. Error Handling - Improved reliability
7. Image Support - More advanced functionality
8. Security Features - Important for sensitive applications 
import bluetooth
import struct
import time
from machine import Pin, PWM
from micropython import const

# Debug flag
dbg = 0

# IRQ Events
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# Service/Characteristic UUIDs (16-bit)
_LED_SERVICE_UUID = bluetooth.UUID(0xA100)  # Changed to 16-bit UUID format
_RGB_CHAR_UUID = bluetooth.UUID(0xA101)
_STATUS_CHAR_UUID = bluetooth.UUID(0xA102)

# BLE Flags
_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

class BLELEDPeripheral:
    def __init__(self, name="BLE-LED"):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._name = name  # Store name for reconnection
        
        # Initialize RGB LED pins (PWM) - Using correct pins from conversion-to-lights.py
        self._red = PWM(Pin(17))    # GP17
        self._green = PWM(Pin(22))  # GP22
        self._blue = PWM(Pin(16))   # GP16
        
        # Set PWM frequency
        pwm_freq = 1000
        self._red.freq(pwm_freq)
        self._green.freq(pwm_freq)
        self._blue.freq(pwm_freq)
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        # Connection state
        self._connected = False
        self._current_rgb = (0, 0, 0)
        
        # Register GATT service
        self._register_services()
        
        # Start advertising
        self._advertise()
        
        # Initialize all LEDs to off
        self._set_rgb(0, 0, 0)
        
        if dbg:
            print("[*] BLE LED Peripheral initialized")

    def _set_lights(self, pin, brightness):
        """Convert 0-255 brightness to duty cycle."""
        realBrightness = int(int(brightness) * (float(65025 / 255.0)))
        pin.duty_u16(realBrightness)

    def _set_rgb(self, r, g, b):
        """Set RGB LED values (0-255)."""
        self._set_lights(self._red, r)
        self._set_lights(self._green, g)
        self._set_lights(self._blue, b)
        self._current_rgb = (r, g, b)
        self._update_status(f"RGB: ({r},{g},{b})")
        if dbg != 0:
            print(f"[*] RGB updated: ({r}, {g}, {b})")

    def _register_services(self):
        """Register LED service and characteristics."""
        # RGB characteristic
        rgb_char = (
            _RGB_CHAR_UUID,
            _FLAG_READ | _FLAG_WRITE
        )
        
        # Status characteristic
        status_char = (
            _STATUS_CHAR_UUID,
            _FLAG_READ | _FLAG_NOTIFY
        )
        
        # LED Service
        led_service = (
            _LED_SERVICE_UUID,
            (rgb_char, status_char,)
        )
        
        # Register service
        ((self._handle_rgb, self._handle_status,),) = self._ble.gatts_register_services((led_service,))
        
        # Set initial values
        self._ble.gatts_write(self._handle_rgb, struct.pack('BBB', 0, 0, 0))
        self._ble.gatts_write(self._handle_status, 'Ready'.encode())
        
        if dbg:
            print("[*] Services registered")

    def _advertise(self):
        """Start advertising LED service."""
        payload = bytearray()
        
        # Add flags
        payload.extend(struct.pack('BB', 2, 0x01))
        payload.extend(b'\x06')  # General discoverable, BR/EDR not supported
        
        # Add name
        name_bytes = self._name.encode()
        payload.extend(struct.pack('BB', len(name_bytes) + 1, 0x09))
        payload.extend(name_bytes)
        
        # Add 16-bit service UUID
        payload.extend(struct.pack('BBH', 3, 0x03, 0xA100))
        
        # Start advertising
        self._ble.gap_advertise(100000, adv_data=payload)
        if dbg:
            print("[*] Advertising started")

    def _update_status(self, status):
        """Update status characteristic."""
        self._ble.gatts_write(self._handle_status, status.encode())

    def _irq(self, event, data):
        """Handle BLE events."""
        if event == _IRQ_CENTRAL_CONNECT:
            # Central device connected
            conn_handle, addr_type, addr = data
            self._connected = True
            if dbg:
                print(f"[+] Connected to central: {bytes(addr).hex()}")
            self._update_status("Connected")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            # Central device disconnected
            conn_handle, addr_type, addr = data
            self._connected = False
            if dbg:
                print(f"[-] Disconnected from central: {bytes(addr).hex()}")
            self._update_status("Ready")
            # Restart advertising
            self._advertise()
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            
            if attr_handle == self._handle_rgb:
                if dbg != 0:
                    print(f"[+] Write Detected to RGB attribute {attr_handle}")
                # Read RGB values
                rgb_data = self._ble.gatts_read(self._handle_rgb)
                if dbg != 0:
                    print(f"RGB Data:\t\t{rgb_data}")   # Note: The Data being received via Bleep is "R\tG\B\n"; will require parsing incoming data
                if len(rgb_data) == 3:
                    r, g, b = struct.unpack('BBB', rgb_data)
                    self._set_rgb(r, g, b)
                else:
                    #test_split = str(rgb_data).split('\t')
                    test_split = rgb_data.decode("utf-8").replace('\n', '').split('\t')
                    if dbg != 0:
                        print(f"Split Time:\t{test_split}")
                    if test_split[0] == "Red":
                        red = 0
                        green = 0
                        blue = 0
                    else:
                        red = int(test_split[0])
                        green = int(test_split[1])
                        blue = int(test_split[2])
                    #self._set_rgb(test_split[0], test_split[1], test_split[2])
                    self._set_rgb(red, green, blue)
            else:
                if dbg != 0:
                    print(f"[-] Write Detected to attribute: {attr_handle}")

    def run(self):
        """Main loop."""
        try:
            while True:
                # Blink status LED when connected
                if self._connected:
                    self.led.toggle()
                else:
                    self.led.off()
                time.sleep_ms(500)
                
        except KeyboardInterrupt:
            print("\n[-] Stopping LED peripheral")
            # Turn off LEDs
            self._set_rgb(0, 0, 0)
            self._ble.active(False)
    
    # Function for Tokenizing RGB Array data
    def parse_rgb(rgb_input_byte_string): 
        # Extract the pieces of RGB information 
        if len(rgb_input_byte_string) < 1: 
            red_led_pwm = 0 
            green_led_pwm = 0 
            blue_led_pwm = 0 
        elif len(rgb_input_byte_string) < 2: 
            red_led_pwm = rgb_input_byte_string[0] 
            green_led_pwm = 0 
            blue_led_pwm = 0 
        elif len(rgb_input_byte_string) < 3: 
            red_led_pwm = rgb_input_byte_string[0] 
            green_led_pwm = rgb_input_byte_string[1] 
            blue_led_pwm = 0 
        elif len(rgb_input_byte_string) < 4: 
            red_led_pwm = rgb_input_byte_string[0] 
            green_led_pwm = rgb_input_byte_string[1] 
            blue_led_pwm = rgb_input_byte_string[2] 
        else: 
            red_led_pwm = rgb_input_byte_string[0] 
            green_led_pwm = rgb_input_byte_string[1] 
            blue_led_pwm = rgb_input_byte_string[2] 
            trash_data = rgb_input_byte_string[2:] # Debug print-out
        if dbg != 0:
            print("[+] Parsed RGB of {0} into R [ {1} ], G [ {2} ], B [ {3} ]".format(rgb_input_byte_string, red_led_pwm, green_led_pwm, blue_led_pwm)) 
        # Return LED PWM values 
        return red_led_pwm, green_led_pwm, blue_led_pwm

def demo():
    """Demo the LED peripheral."""
    led_dev = BLELEDPeripheral()
    try:
        led_dev.run()
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        led_dev._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting BLE LED Peripheral")
    demo()

'''
Usage Example:

# Create and run LED peripheral
led_dev = BLELEDPeripheral()
led_dev.run()
'''
import bluetooth
from machine import Pin, SPI
import struct
import time
from micropython import const
from ble_advertising import advertising_payload
import framebuf

# Debugging flag
dbg = 1

# IRQ Event Constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)

# Flag Constants
_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# Service UUID for E-Ink Display Demo
_EINK_UUID = bluetooth.UUID("E1234000-A5A5-F5F5-C5C5-111122223333")

# Read Characteristics
_READ_BUFFER = (
    bluetooth.UUID("E1234001-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_READ | _FLAG_NOTIFY,
)

_READ_STATUS = (
    bluetooth.UUID("E1234002-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_READ,
)

# Write Characteristics
_WRITE_DISPLAY = (
    bluetooth.UUID("E1234003-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_WRITE,
)

_WRITE_COMMAND = (
    bluetooth.UUID("E1234004-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_WRITE,
)

# Combine all characteristics into one service
_EINK_SERVICE = (
    _EINK_UUID,
    (_READ_BUFFER, _READ_STATUS, _WRITE_DISPLAY, _WRITE_COMMAND),
)

# Display resolution Definitions
EPD_WIDTH  = 122
EPD_HEIGHT = 250

# Pico W Ping Definitions
VCC_PIN = 39        # Pin 39 (VSYS)
GND_PIN = 38        # Pin 38 (GND)
DIN_PIN = 11        # Pin 15 (GP11/SPI1_TX)
CLK_PIN = 10        # Pin 14 (GP10/SPI1_SCK)
CS_PIN = 9          # Pin 12 (GP9/SPI1_CSn)
DC_PIN = 8          # Pin 11 (GP8/SPI1_RX)
RST_PIN = 12        # Pin 16 (GP12/SPI1_RX)
BUSY_PIN = 13       # Pin 17 (GP13/SPI1_CSn)

## E-Ink Class Definition
class EPD_2in13_V4(framebuf.FrameBuffer):
    def __init__(self):
        print("[*] Initializing E-Ink display")
        
        # Pin setup
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        
        # Handle width alignment
        self.width = EPD_WIDTH if EPD_WIDTH % 8 == 0 else (EPD_WIDTH // 8) * 8 + 8
        self.height = EPD_HEIGHT
        
        # Initialize SPI
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        
        # Framebuffer setup
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init()
        print("[+] Display initialized")

    def reset(self):
        self.reset_pin.value(1)
        time.sleep_ms(20)
        self.reset_pin.value(0)
        time.sleep_ms(2)
        self.reset_pin.value(1)
        time.sleep_ms(20)

    def wait_busy(self):
        print('[*] Waiting for display ready')
        while self.busy_pin.value():
            time.sleep_ms(10)
        print('[+] Display ready')

    def send_command(self, cmd):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytes([cmd]))
        self.cs_pin.value(1)

    def send_data(self, data):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytes([data]))
        self.cs_pin.value(1)

    def init(self):
        print('[*] Starting display initialization')
        self.reset()
        time.sleep_ms(100)
        
        self.wait_busy()
        self.send_command(0x12)  # SWRESET
        self.wait_busy()
        
        self.send_command(0x01)  # Driver output control 
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  # Data entry mode
        self.send_data(0x03)
        
        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)
        
        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.wait_busy()
        print('[+] Initialization complete')

    def display_frame(self):
        """Update display with current framebuffer contents"""
        self.send_command(0x24)  # Write RAM
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(self.buffer)
        self.cs_pin.value(1)
        
        self.send_command(0x22)  # Display update control
        self.send_data(0xF7)
        self.send_command(0x20)  # Activate display update
        self.wait_busy()

    def clear(self):
        """Clear display to white with safe timing"""
        self.fill(0xFF)  # White
        self.display_frame()
        time.sleep(3)  # Safe delay to prevent burn-in

    def display_text(self, text, x=10, y=10):
        """Display text with safe clearing afterward"""
        self.fill(0xFF)  # White background
        
        # Handle multiline text
        lines = text.split('\n')
        current_y = y
        for line in lines:
            self.text(line, x, current_y, 0)  # Black text
            current_y += 12
        
        self.display_frame()
        time.sleep(3)  # Wait before clearing
        self.clear()  # Safe clear after display

    def sleep(self):
        """Enter deep sleep mode"""
        self.send_command(0x10)
        self.send_data(0x01)
        time.sleep_ms(100)

## BLE Class Definition
class BLEEinkDisplay:
    def __init__(self, ble, eink_display, name="eink-display"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._eink = eink_display  # E-ink display object
        
        # Register services
        ((self._handle_read_buffer,
          self._handle_read_status,
          self._handle_write_display,
          self._handle_write_command),) = self._ble.gatts_register_services((_EINK_SERVICE,))
        
        # Initialize characteristics
        self._ble.gatts_write(self._handle_read_buffer, b'Empty Buffer')
        self._ble.gatts_write(self._handle_read_status, b'Ready')
        
        self._connections = set()
        self._read_buffer = ""
        self._display_text = ""
        
        # Split advertising to stay within size limits
        adv_data = advertising_payload(services=[_EINK_UUID])
        resp_data = advertising_payload(name=name)
        self._ble.gap_advertise(500000, adv_data=adv_data, resp_data=resp_data)
        
        if dbg:
            print("[+] BLE E-Ink Display service initialized")

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            if dbg:
                print(f"[+] Connected: {conn_handle}")
            self._connections.add(conn_handle)
            self._update_status("Connected")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if dbg:
                print(f"[-] Disconnected: {conn_handle}")
            self._connections.remove(conn_handle)
            self._update_status("Disconnected")
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            value = self._ble.gatts_read(attr_handle)
            
            if attr_handle == self._handle_write_display:
                if dbg:
                    print(f"[*] Display write: {value}")
                self._display_text = value.decode()
                self._eink.display_text(self._display_text)
                self._update_status("Display updated")
                
            elif attr_handle == self._handle_write_command:
                if dbg:
                    print(f"[*] Command write: {value}")
                self._handle_command(value.decode())

        elif event == _IRQ_GATTS_READ_REQUEST:
            conn_handle, attr_handle = data
            if dbg:
                print(f"[*] Read request - handle: {attr_handle}")
            
            if attr_handle == self._handle_read_buffer:
                self._update_read_buffer()

    def _update_status(self, status):
        if dbg:
            print(f"[*] Status: {status}")
        self._ble.gatts_write(self._handle_read_status, status.encode())

    def _update_read_buffer(self):
        """Update read buffer with current display state"""
        buffer_text = f"Display: {self._display_text}"
        self._ble.gatts_write(self._handle_read_buffer, buffer_text.encode())
        if dbg:
            print(f"[*] Buffer updated: {buffer_text}")

    def _handle_command(self, cmd):
        """Handle display commands"""
        if cmd == "clear":
            self._eink.clear()
            self._display_text = ""
            self._update_status("Display cleared")
        elif cmd == "refresh":
            self._eink.display_frame()
            self._update_status("Display refreshed")
        else:
            self._update_status(f"Unknown command: {cmd}")

    def _advertise(self, interval_us=500000):
        adv_data = advertising_payload(services=[_EINK_UUID])
        self._ble.gap_advertise(interval_us, adv_data=adv_data) 

## Main Code

# Demo Function
def demo():
    print("[*] Starting E-ink Display Demo")
    
    # Initialize display with verification
    epd = EPD_2in13_V4()
    if not epd.init():
        print("[-] Display initialization failed!")
        return
        
    # Test pattern
    print("[*] Drawing test pattern...")
    epd.fill(0xFF)  # White background
    epd.rect(0, 0, EPD_WIDTH, EPD_HEIGHT, 0)  # Black border
    epd.text("Display Test", 10, 10, 0)
    epd.display_frame()
    
    print("[*] Starting BLE service...")
    ble = bluetooth.BLE()
    ble_display = BLEEinkDisplay(ble, epd)
    
    # Onboard LED for status
    led = Pin("LED", Pin.OUT)
    
    print("[+] Ready for connections")
    epd.display_text("Ready for\nBLE connections")
    
    try:
        while True:
            if ble_display._connections:
                led.toggle()  # Blink when connected
            else:
                led.off()
            time.sleep_ms(500)
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        epd.clear()
        ble.active(False)

if __name__ == "__main__":
    print("[*] Starting E-ink Display BLE Demo")
    demo() 
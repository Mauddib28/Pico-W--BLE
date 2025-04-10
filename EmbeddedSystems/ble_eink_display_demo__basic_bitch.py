import bluetooth
from machine import Pin, SPI
import struct
import time
from micropython import const
from ble_advertising import advertising_payload
import framebuf
# Import for display to Waveshare E-Ink Display
from Pico_ePaper_2_13_V4 import EPD_2in13_V4_Portrait, EPD_2in13_V4_Landscape

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

# Test Display Function
def test_display():
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()
    
    epd.fill(0xff)
    epd.text("Waveshare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 20, 0x00)
    epd.text("Raspberry Pico", 0, 30, 0x00)
    epd.text("Hello World", 0, 40, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.vline(5, 55, 60, 0x00)
    epd.vline(100, 55, 60, 0x00)
    epd.hline(5, 55, 95, 0x00)
    epd.hline(5, 115, 95, 0x00)
    epd.line(5, 55, 100, 115, 0x00)
    epd.line(100, 55, 5, 115, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.rect(130, 10, 40, 80, 0x00)
    epd.fill_rect(190, 10, 40, 80, 0x00)
    epd.Display_Base(epd.buffer)
    epd.delay_ms(2000)
    
    epd.init()
    for i in range(0, 10):
        epd.fill_rect(175, 105, 10, 10, 0xff)
        epd.text(str(i), 177, 106, 0x00)
        epd.displayPartial(epd.buffer)
        
    print("sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()
    
    
    
    epd = EPD_2in13_V4_Portrait()
    epd.Clear()
    
    epd.fill(0xff)
    epd.text("Waveshare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 30, 0x00)
    epd.text("Raspberry Pico", 0, 50, 0x00)
    epd.text("Hello World", 0, 70, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.vline(10, 90, 60, 0x00)
    epd.vline(90, 90, 60, 0x00)
    epd.hline(10, 90, 80, 0x00)
    epd.hline(10, 150, 80, 0x00)
    epd.line(10, 90, 90, 150, 0x00)
    epd.line(90, 90, 10, 150, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.rect(10, 180, 50, 40, 0x00)
    epd.fill_rect(60, 180, 50, 40, 0x00)
    epd.Display_Base(epd.buffer)
    epd.delay_ms(2000)
    
    epd.init()
    for i in range(0, 10):
        epd.fill_rect(40, 230, 40, 10, 0xff)
        epd.text(str(i), 60, 230, 0x00)
        epd.displayPartial(epd.buffer)
        
    print("sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()

# Demo Function
def demo():
    print("[*] Starting E-ink Display Demo")
    
    # Initialize display with verification
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()
    #if not epd.init():
    #    print("[-] Display initialization failed!")
    #    return
        
    # Test pattern
    print("[*] Drawing test pattern...")
    epd.fill(0xFF)  # White background
    #epd.rect(0, 0, EPD_WIDTH, EPD_HEIGHT, 0)  # Black border
    #epd.text("Display Test", 10, 10, 0)
    epd.text("WaveShare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 30, 0x00)
    epd.text("Raspberry Pico WH", 0, 50, 0x00)
    epd.text("Bluetooth Low Energy", 0, 70, 0x00)
    epd.text("   GATT Server", 0, 80, 0x00)
    #epd.display_frame()
    epd.display(epd.buffer)
    epd.delay_ms(2000)

    # Sleep the Display
    print("E-Ink Sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()     # Causes a deep-sleep state
    
    print("[*] Starting BLE service...")
    ble = bluetooth.BLE()
    ble_display = BLEEinkDisplay(ble, epd)
    
    # Onboard LED for status
    led = Pin("LED", Pin.OUT)
    
    print("[+] Ready for connections")
    #epd.display_text("Ready for\nBLE connections")
    epd.display_text("Ready for BLE")
    
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
    #test_display()
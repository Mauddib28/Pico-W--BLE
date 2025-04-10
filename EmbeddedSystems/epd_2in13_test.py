import framebuf
from machine import Pin, SPI
import time

# Display resolution
EPD_WIDTH  = 122
EPD_HEIGHT = 250

class EPD_2in13:
    def __init__(self):
        """
        Pin Layout for Pico W to Waveshare 2.13" E-Ink HAT:
        
        Display HAT -> Pico W
        -----------------------------
        BUSY -> GP13 (Pin 17)
        RST  -> GP12 (Pin 16)
        DC   -> GP8  (Pin 11)
        CS   -> GP9  (Pin 12)
        CLK  -> GP10 (Pin 14) [SPI1 SCK]
        DIN  -> GP11 (Pin 15) [SPI1 TX]
        GND  -> GND  (Pin 38)
        VCC  -> 3V3  (Pin 36)
        """
        print("[*] Initializing E-Ink display")
        
        # Pin definitions
        self.busy_pin = Pin(13, Pin.IN)  # Changed
        self.rst_pin = Pin(12, Pin.OUT)  # Changed
        self.dc_pin = Pin(8, Pin.OUT)    # Changed
        self.cs_pin = Pin(9, Pin.OUT)    # Changed
        
        # Initialize SPI
        self.spi = SPI(1,
                      baudrate=4000000,
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=SPI.MSB,
                      sck=Pin(10),
                      mosi=Pin(11))
        
        # Initialize pins
        self.cs_pin.value(1)
        self.dc_pin.value(0)
        self.rst_pin.value(0)
        
        # Initialize framebuffer
        self.buffer = bytearray(EPD_WIDTH * EPD_HEIGHT // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init_display()
        print("[+] Display initialized")

    def reset(self):
        """Hardware reset sequence"""
        print("[*] Resetting display")
        self.rst_pin.value(1)
        time.sleep_ms(200)  # Increased delay
        self.rst_pin.value(0)
        time.sleep_ms(20)   # Increased delay
        self.rst_pin.value(1)
        time.sleep_ms(200)  # Increased delay

    def wait_busy(self):
        """Wait until BUSY pin is low"""
        print("[*] Waiting for display to be ready")
        while self.busy_pin.value():
            time.sleep_ms(100)  # Increased delay
        print("[+] Display ready")

    def send_command(self, command):
        """Send command byte to display"""
        self.cs_pin.value(0)
        self.dc_pin.value(0)
        self.spi.write(bytes([command]))
        self.cs_pin.value(1)
        time.sleep_ms(1)  # Added delay

    def send_data(self, data):
        """Send data byte to display"""
        self.cs_pin.value(0)
        self.dc_pin.value(1)
        self.spi.write(bytes([data]))
        self.cs_pin.value(1)
        time.sleep_ms(1)  # Added delay

    def init_display(self):
        """Initialize display with manufacturer settings"""
        print("[*] Starting display initialization")
        self.reset()
        
        # Power on sequence
        self.send_command(0x04)
        self.wait_busy()
        print("[+] Power on complete")
        
        # Booster soft start
        self.send_command(0x00)  # panel setting
        self.send_data(0x1F)     # KW-BF   KWR-AF  BWROTP 0f
        self.send_data(0x0D)     # VCOM to 0V fast
        
        # Power setting
        self.send_command(0x01)  # Power setting
        self.send_data(0x03)     # VDS_EN, VDG_EN
        self.send_data(0x00)     # VCOM_HV, VGHL_LV=16V
        self.send_data(0x2B)     # VDH=11V
        self.send_data(0x2B)     # VDL=11V
        
        # Power optimization
        self.send_command(0x06)  # Booster soft start
        self.send_data(0x17)     # A
        self.send_data(0x17)     # B
        self.send_data(0x17)     # C
        
        self.send_command(0xF8)  # POWER SETTING
        self.send_data(0x60)
        self.send_data(0xA5)
        
        self.send_command(0x16)  # POWER ON
        self.send_data(0x00)
        
        self.send_command(0x50)  # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x97)     # Border waveform control
        
        print("[+] Initialization sequence complete")

    def display_frame(self):
        """Update display with current framebuffer"""
        print("[*] Updating display")
        
        self.send_command(0x10)  # Start transmission 1
        for i in range(0, EPD_WIDTH * EPD_HEIGHT // 8):
            self.send_data(self.buffer[i])
        
        self.send_command(0x13)  # Start transmission 2
        for i in range(0, EPD_WIDTH * EPD_HEIGHT // 8):
            self.send_data(self.buffer[i])
            
        self.send_command(0x12)  # Display refresh
        time.sleep_ms(100)
        self.wait_busy()
        print("[+] Display updated")

    def clear(self, color=0xFF):
        """Clear display to white (0xFF) or black (0x00)"""
        print("[*] Clearing display")
        self.fb.fill(color)
        self.display_frame()

class EPD_Debug:
    def __init__(self):
        print("[*] Starting debug initialization")
        
        # Pin setup with debug prints
        print("[*] Setting up pins...")
        self.busy_pin = Pin(13, Pin.IN)
        self.rst_pin = Pin(12, Pin.OUT)
        self.dc_pin = Pin(8, Pin.OUT)
        self.cs_pin = Pin(9, Pin.OUT)
        
        # Initial pin states
        self.cs_pin.value(1)    # CS high
        self.dc_pin.value(0)    # DC low
        print("[+] Pins configured")
        
        # SPI setup with explicit parameters
        print("[*] Initializing SPI...")
        self.spi = SPI(1,
                      baudrate=2000000,  # Slower speed for testing
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=SPI.MSB,
                      sck=Pin(10),
                      mosi=Pin(11))
        print("[+] SPI initialized")
        
        # Test basic communication
        self.test_communication()
    
    def test_communication(self):
        """Basic communication test"""
        print("\n=== Testing Basic Communication ===")
        
        print("[*] Testing BUSY pin...")
        busy_state = self.busy_pin.value()
        print(f"[+] BUSY pin state: {busy_state}")
        
        print("[*] Performing reset sequence...")
        self.reset()
        
        print("[*] Testing basic command send...")
        try:
            # Power on command
            self.send_command(0x04)
            print("[+] Command sent successfully")
            
            # Wait for busy
            print("[*] Checking BUSY response...")
            timeout = 100  # 10 second timeout
            while timeout > 0 and self.busy_pin.value():
                time.sleep_ms(100)
                timeout -= 1
            if timeout > 0:
                print("[+] BUSY pin responded correctly")
            else:
                print("[-] BUSY timeout - no response")
                
        except Exception as e:
            print(f"[-] Command test failed: {e}")
    
    def reset(self):
        """Hardware reset with debug"""
        print("[*] Reset pin HIGH")
        self.rst_pin.value(1)
        time.sleep_ms(200)
        print("[*] Reset pin LOW")
        self.rst_pin.value(0)
        time.sleep_ms(200)
        print("[*] Reset pin HIGH")
        self.rst_pin.value(1)
        time.sleep_ms(200)
    
    def send_command(self, cmd):
        """Send command with debug"""
        print(f"[*] Sending command: 0x{cmd:02X}")
        self.cs_pin.value(0)  # CS low
        self.dc_pin.value(0)  # DC low (command)
        self.spi.write(bytes([cmd]))
        self.cs_pin.value(1)  # CS high
        time.sleep_ms(10)
    
    def send_data(self, data):
        """Send data with debug"""
        print(f"[*] Sending data: 0x{data:02X}")
        self.cs_pin.value(0)  # CS low
        self.dc_pin.value(1)  # DC high (data)
        self.spi.write(bytes([data]))
        self.cs_pin.value(1)  # CS high
        time.sleep_ms(10)

    def init_sequence(self):
        """Try basic initialization sequence"""
        print("\n=== Starting Init Sequence ===")
        
        self.reset()
        time.sleep_ms(100)
        
        # Power on
        print("[*] Sending power on command")
        self.send_command(0x04)
        time.sleep_ms(100)
        
        # Panel setting
        print("[*] Configuring panel")
        self.send_command(0x00)
        self.send_data(0x1F)
        
        # Try to clear display
        print("[*] Attempting display clear")
        self.send_command(0x10)  # Data start
        for i in range(4000):  # Send white data
            self.send_data(0xFF)
        
        self.send_command(0x12)  # Refresh
        time.sleep_ms(100)
        print("[+] Init sequence complete")

def run_test():
    print("\n=== Starting E-Ink Display Debug ===\n")
    
    epd = EPD_Debug()
    
    # Wait a moment
    time.sleep(1)
    
    # Try initialization
    epd.init_sequence()
    
    print("\n=== Debug Complete ===")
    print("Check serial output for communication status")

if __name__ == "__main__":
    run_test() 
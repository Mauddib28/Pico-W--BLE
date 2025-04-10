from machine import Pin, SPI
import framebuf
import time

# Display resolution
EPD_WIDTH  = 122
EPD_HEIGHT = 250

class EPD_2in13_V4:
    def __init__(self):
        # Pin definitions
        self.reset_pin = Pin(12, Pin.OUT)
        self.dc_pin = Pin(8, Pin.OUT)
        self.cs_pin = Pin(9, Pin.OUT)
        self.busy_pin = Pin(13, Pin.IN)
        
        # SPI initialization
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        
        # Framebuffer
        self.buffer = bytearray(EPD_WIDTH * EPD_HEIGHT // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init()
        
    def reset(self):
        self.reset_pin.value(1)
        time.sleep_ms(20)
        self.reset_pin.value(0)
        time.sleep_ms(2)
        self.reset_pin.value(1)
        time.sleep_ms(20)

    def send_command(self, command):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytes([command]))
        self.cs_pin.value(1)

    def send_data(self, data):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytes([data]))
        self.cs_pin.value(1)

    def wait_until_idle(self):
        while self.busy_pin.value() == 1:
            time.sleep_ms(10)

    def init(self):
        self.reset()
        
        self.send_command(0x12)  # SWRESET
        self.wait_until_idle()
        
        self.send_command(0x01)  # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  # Data entry mode
        self.send_data(0x03)
        
        self.send_command(0x44)  # Set RAM X start/end
        self.send_data(0x00)
        self.send_data(0x0F)
        
        self.send_command(0x45)  # Set RAM Y start/end
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x3C)  # Border waveform
        self.send_data(0x05)
        
        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18)  # Temperature sensor control
        self.send_data(0x80)
        
        self.clear()

    def display_text(self, text, x=10, y=10):
        """Display text on the E-ink screen"""
        self.fb.fill(0xFF)  # Clear to white
        lines = text.split('\n')
        current_y = y
        
        for line in lines:
            self.fb.text(line, x, current_y, 0)  # Black text
            current_y += 12  # Line spacing
            
        self.display_frame()

    def clear(self):
        """Clear the display to white"""
        self.fb.fill(0xFF)
        self.display_frame()

    def display_frame(self):
        """Update the display with current framebuffer contents"""
        self.send_command(0x24)  # Write RAM
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(self.buffer)
        self.cs_pin.value(1)
        
        self.send_command(0x22)  # Display update control
        self.send_data(0xF7)
        self.send_command(0x20)  # Activate display update
        self.wait_until_idle()

    def refresh(self):
        """Force a refresh of the display"""
        self.display_frame() 
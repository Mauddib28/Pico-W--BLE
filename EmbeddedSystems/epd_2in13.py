from machine import Pin, SPI
import framebuf
import time

EPD_WIDTH = 122
EPD_HEIGHT = 250

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

class EPD_2in13_V4(framebuf.FrameBuffer):
    def __init__(self):
        # Pin setup
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        
        # Initialize SPI
        self.spi = SPI(1,
                      baudrate=4000000,
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=SPI.MSB,
                      sck=Pin(10),
                      mosi=Pin(11))
        
        # Buffer setup
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.buffer = bytearray(self.height * int(self.width / 8))
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init()

    def digital_read(self, pin):
        return pin.value()
        
    def digital_write(self, pin, value):
        pin.value(value)
        
    def delay_ms(self, delaytime):
        time.sleep_ms(delaytime)

    def spi_writebyte(self, data):
        self.spi.write(bytes([data]))
        
    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte(command)
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte(data)
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        """Send data buffer to display"""
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        # Convert to bytearray if not already
        if isinstance(buf, list):
            buf = bytearray(buf)
        self.spi.write(buf)
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        while(self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)
        print('busy release')

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)
        
        self.send_command(0x45)
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)

    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)
        self.send_data(Xstart & 0xFF)
        
        self.send_command(0x4F)
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)
        
        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()
        
        self.send_command(0x01)  # Driver output control 
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  # Data entry mode
        self.send_data(0x03)
        
        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)
        
        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.ReadBusy()

    def display(self, buffer):
        self.send_command(0x24)
        self.send_data1(buffer)
        
        self.send_command(0x22)
        self.send_data(0xF7)
        self.send_command(0x20)
        self.ReadBusy()

    def Clear(self):
        """Clear display to white"""
        buf = bytearray([0xff] * (self.height * int(self.width / 8)))
        self.send_command(0x24)
        self.send_data1(buf)
        
        self.send_command(0x22)
        self.send_data(0xF7)
        self.send_command(0x20)
        self.ReadBusy()

    def sleep(self):
        self.send_command(0x10)
        self.send_data(0x01) 
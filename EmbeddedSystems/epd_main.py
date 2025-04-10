from epd_2in13 import EPD_2in13_V4
import time

def test():
    epd = EPD_2in13_V4()
    
    # Clear to white
    epd.Clear()
    time.sleep_ms(1000)
    
    # Draw some text
    epd.fill(0xff)  # White background
    epd.text("Hello World!", 10, 10, 0x00)  # Black text
    epd.text("E-Paper Test", 10, 30, 0x00)
    epd.display(epd.buffer)
    time.sleep_ms(2000)
    
    # Clear before sleep
    epd.Clear()
    epd.sleep()

if __name__ == "__main__":
    test() 
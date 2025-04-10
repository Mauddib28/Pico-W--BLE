import bluetooth
from machine import Pin
import time
from waveshare_epaper import EPD_2in13_V4
from ble_eink_display_demo import BLEEinkDisplay

def demo():
    print("[*] Initializing E-ink display...")
    epd = EPD_2in13_V4()
    epd.clear()
    
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
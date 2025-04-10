from machine import I2C, Pin, SPI
import bluetooth
import struct
import time
from micropython import const
from array import array

# Debug flag
dbg = 1

# I2C Configuration
I2C_SDA = 0  # GP0
I2C_SCL = 1  # GP1
I2C_FREQ = 400_000  # 400kHz

# Audio DAC Configuration (example for PCM5102)
PCM5102_ADDR = const(0x4D)
PCM5102_FORMAT = const(0x02)  # I2S format register
PCM5102_VOLUME = const(0x03)  # Volume control register

# L2CAP Configuration
_L2CAP_PSM = const(0x70)
_L2CAP_MTU = const(512)

# Audio Buffer Configuration
BUFFER_SIZE = 4096
CHUNK_SIZE = 256  # Size of each audio chunk to process

# Circular buffer for audio data
class AudioBuffer:
    def __init__(self, size):
        self.buffer = array('B', [0] * size)
        self.size = size
        self.write_ptr = 0
        self.read_ptr = 0
        self.count = 0

class BLEI2CAudioBridge:
    def __init__(self):
        # Initialize BLE
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Initialize I2C
        self.i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
        
        # Audio buffer (circular buffer implementation)
        self._buffer = AudioBuffer(BUFFER_SIZE)
        
        # L2CAP state
        self._l2cap_connected = False
        self._l2cap_conn_handle = None
        self._l2cap_channel = None
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        # Initialize audio DAC
        self._init_audio_dac()
        
        if dbg:
            print("[*] BLE I2C Audio Bridge initialized")
            print(f"[*] I2C devices found: {self.i2c.scan()}")
            
    def _init_audio_dac(self):
        """Initialize the PCM5102 or similar DAC."""
        try:
            # Example configuration for PCM5102
            self.i2c.writeto_mem(PCM5102_ADDR, PCM5102_FORMAT, bytes([0x02]))  # I2S format
            self.i2c.writeto_mem(PCM5102_ADDR, PCM5102_VOLUME, bytes([0xFF]))  # Max volume
            if dbg:
                print("[+] Audio DAC initialized")
        except Exception as e:
            print(f"[-] DAC initialization error: {e}")

    def _irq(self, event, data):
        """Handle BLE events."""
        if event == _IRQ_L2CAP_ACCEPT:
            conn_handle, psm = data
            return 0  # Accept connection
            
        elif event == _IRQ_L2CAP_CONNECT:
            conn_handle, mtu, cid = data
            self._l2cap_connected = True
            self._l2cap_conn_handle = conn_handle
            self._l2cap_channel = cid
            if dbg:
                print("[+] L2CAP connected")
            
        elif event == _IRQ_L2CAP_DISCONNECT:
            self._l2cap_connected = False
            self._l2cap_channel = None
            if dbg:
                print("[-] L2CAP disconnected")
            
        elif event == _IRQ_L2CAP_RECV:
            # Handle incoming audio data
            self._handle_audio_data()

    def _handle_audio_data(self):
        """Process incoming L2CAP audio data."""
        if not self._l2cap_connected:
            return
            
        try:
            # Create buffer for receiving
            data = bytearray(_L2CAP_MTU)
            # Read data
            bytes_read = self._ble.l2cap_recvinto(
                self._l2cap_conn_handle,
                self._l2cap_channel,
                data
            )
            
            if bytes_read > 0:
                # Add to circular buffer
                self._add_to_buffer(data[:bytes_read])
                
        except Exception as e:
            print(f"[-] Error receiving data: {e}")

    def _add_to_buffer(self, data):
        """Add data to circular buffer."""
        for byte in data:
            if self._buffer.count < self._buffer.size:
                self._buffer.buffer[self._buffer.write_ptr] = byte
                self._buffer.write_ptr = (self._buffer.write_ptr + 1) % self._buffer.size
                self._buffer.count += 1

    def _get_from_buffer(self, size):
        """Get data from circular buffer."""
        if self._buffer.count < size:
            return None
            
        data = bytearray(size)
        for i in range(size):
            data[i] = self._buffer.buffer[self._buffer.read_ptr]
            self._buffer.read_ptr = (self._buffer.read_ptr + 1) % self._buffer.size
            self._buffer.count -= 1
            
        return data

    def process_audio(self):
        """Process and output audio data."""
        while True:
            if self._buffer.count >= CHUNK_SIZE:
                chunk = self._get_from_buffer(CHUNK_SIZE)
                if chunk:
                    try:
                        # Send to DAC via I2C
                        self.i2c.writeto(PCM5102_ADDR, chunk)
                        self.led.toggle()  # Visual indicator
                    except Exception as e:
                        print(f"[-] Error writing to DAC: {e}")
            else:
                # Small delay when buffer is low
                time.sleep_ms(1)

    def start(self):
        """Start the audio bridge."""
        if dbg:
            print("[*] Starting audio bridge")
            print("[*] Waiting for L2CAP connection...")
        
        # Start advertising
        self._advertise()
        
        # Main processing loop
        while True:
            if self._l2cap_connected:
                self.process_audio()
            time.sleep_ms(10)

    def _advertise(self, interval_us=100000):
        """Start advertising."""
        payload = bytearray()
        # Add flags
        payload.extend(struct.pack('BB', 2, 0x01))
        payload.extend(b'\x06')
        # Add name
        name = "BLE-Audio"
        payload.extend(struct.pack('BB', len(name) + 1, 0x09))
        payload.extend(name.encode())
        
        self._ble.gap_advertise(interval_us, adv_data=payload)
        if dbg:
            print("[*] Advertising started")

def demo():
    """Demo the BLE I2C audio bridge."""
    bridge = BLEI2CAudioBridge()
    
    try:
        bridge.start()
    except KeyboardInterrupt:
        print("\n[-] Stopping bridge")
        bridge._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting BLE I2C Audio Bridge")
    demo() 
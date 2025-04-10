from machine import I2S, Pin
import bluetooth
import struct
import time
from micropython import const
from array import array

# Debug flag
dbg = 1

# I2S Configuration
I2S_ID = 0  # First I2S peripheral
SCK_PIN = 16  # Serial clock
WS_PIN = 17   # Word select (also called LRCK)
SD_PIN = 18   # Serial data

# I2S Format
BITS_PER_SAMPLE = 16
SAMPLE_RATE_HZ = 44100
SAMPLE_STEREO = True
FORMAT = I2S.STEREO if SAMPLE_STEREO else I2S.MONO

# Buffer Configuration
BUFFER_SIZE = 4096
CHUNK_SIZE = 1024  # Size of each audio chunk

# L2CAP Configuration
_L2CAP_PSM = const(0x70)
_L2CAP_MTU = const(512)

class BLEI2SAudioBridge:
    def __init__(self):
        # Initialize BLE
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Initialize I2S
        self.audio_out = I2S(
            I2S_ID,
            sck=Pin(SCK_PIN),
            ws=Pin(WS_PIN),
            sd=Pin(SD_PIN),
            mode=I2S.TX,
            bits=BITS_PER_SAMPLE,
            format=FORMAT,
            rate=SAMPLE_RATE_HZ,
            ibuf=BUFFER_SIZE
        )
        
        # Audio buffer
        self._buffer = array('h', [0] * BUFFER_SIZE)  # 16-bit buffer
        self._write_ptr = 0
        self._read_ptr = 0
        self._buffer_count = 0
        
        # L2CAP state
        self._l2cap_connected = False
        self._l2cap_conn_handle = None
        self._l2cap_channel = None
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        if dbg:
            print("[*] BLE I2S Audio Bridge initialized")
            print(f"[*] Sample Rate: {SAMPLE_RATE_HZ}Hz")
            print(f"[*] Format: {'Stereo' if SAMPLE_STEREO else 'Mono'}")
            print(f"[*] Bits per Sample: {BITS_PER_SAMPLE}")

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
                # Convert bytes to 16-bit samples
                samples = array('h')
                samples.frombytes(data[:bytes_read])
                self._add_to_buffer(samples)
                
        except Exception as e:
            print(f"[-] Error receiving data: {e}")

    def _add_to_buffer(self, samples):
        """Add samples to circular buffer."""
        for sample in samples:
            if self._buffer_count < BUFFER_SIZE:
                self._buffer[self._write_ptr] = sample
                self._write_ptr = (self._write_ptr + 1) % BUFFER_SIZE
                self._buffer_count += 1

    def _get_from_buffer(self, size):
        """Get samples from circular buffer."""
        if self._buffer_count < size:
            return None
            
        samples = array('h', [0] * size)
        for i in range(size):
            samples[i] = self._buffer[self._read_ptr]
            self._read_ptr = (self._read_ptr + 1) % BUFFER_SIZE
            self._buffer_count -= 1
            
        return samples

    def process_audio(self):
        """Process and output audio data."""
        while True:
            if self._buffer_count >= CHUNK_SIZE:
                chunk = self._get_from_buffer(CHUNK_SIZE)
                if chunk:
                    try:
                        # Write to I2S
                        self.audio_out.write(chunk)
                        self.led.toggle()  # Visual indicator
                    except Exception as e:
                        print(f"[-] Error writing to I2S: {e}")
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
        name = "BLE-I2S-Audio"
        payload.extend(struct.pack('BB', len(name) + 1, 0x09))
        payload.extend(name.encode())
        
        self._ble.gap_advertise(interval_us, adv_data=payload)
        if dbg:
            print("[*] Advertising started")

def demo():
    """Demo the BLE I2S audio bridge."""
    bridge = BLEI2SAudioBridge()
    
    try:
        bridge.start()
    except KeyboardInterrupt:
        print("\n[-] Stopping bridge")
        bridge.audio_out.deinit()
        bridge._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting BLE I2S Audio Bridge")
    demo() 
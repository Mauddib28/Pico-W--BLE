import bluetooth
import struct
import time
from machine import Pin, ADC
from micropython import const

# Debug flag
dbg = 1

# IRQ Events
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)

# Audio Configuration
SAMPLE_RATE = 8000  # Hz
SAMPLE_SIZE = 1     # bytes (8-bit audio)
CHUNK_SIZE = 512    # bytes per transmission
BUFFER_SIZE = 1024  # bytes for circular buffer

# L2CAP Configuration
_L2CAP_PSM = const(0x70)  # Must be even
_L2CAP_MTU = const(512)   # Maximum L2CAP packet size

class BLEAudioL2CAP:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # L2CAP state
        self._l2cap_connected = False
        self._l2cap_conn_handle = None
        self._l2cap_channel = None
        self._send_ready = True
        
        # Audio buffer
        self._buffer = bytearray(BUFFER_SIZE)
        self._buffer_index = 0
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        # Audio input (ADC)
        self.adc = ADC(26)  # GP26 for audio input
        
        if dbg:
            print("[*] Starting L2CAP Audio Demo")
            print(f"[*] Sample Rate: {SAMPLE_RATE} Hz")
            print(f"[*] Buffer Size: {BUFFER_SIZE} bytes")
            print(f"[*] Chunk Size: {CHUNK_SIZE} bytes")
            print(f"[*] Theoretical Latency: {(CHUNK_SIZE/SAMPLE_RATE)*1000:.1f}ms")

    def _irq(self, event, data):
        """Handle BLE and L2CAP events."""
        if event == _IRQ_L2CAP_ACCEPT:
            # L2CAP connection request
            conn_handle, psm = data
            if dbg:
                print(f"[*] L2CAP Accept Request - Handle: {conn_handle}")
            return 0  # Accept connection
            
        elif event == _IRQ_L2CAP_CONNECT:
            # L2CAP channel established
            conn_handle, mtu, cid = data
            if dbg:
                print(f"[+] L2CAP Connected - MTU: {mtu}")
            self._l2cap_connected = True
            self._l2cap_conn_handle = conn_handle
            self._l2cap_channel = cid
            
        elif event == _IRQ_L2CAP_DISCONNECT:
            # L2CAP channel disconnected
            conn_handle, cid, status = data
            if dbg:
                print(f"[-] L2CAP Disconnected")
            self._l2cap_connected = False
            self._l2cap_channel = None
            
        elif event == _IRQ_L2CAP_SEND_READY:
            # Channel ready for sending
            self._send_ready = True

    def start_streaming(self):
        """Start audio streaming."""
        if not self._l2cap_connected:
            print("[-] Not connected")
            return
            
        try:
            last_time = time.ticks_ms()
            samples_per_chunk = CHUNK_SIZE // SAMPLE_SIZE
            
            while self._l2cap_connected:
                current_time = time.ticks_ms()
                elapsed = time.ticks_diff(current_time, last_time)
                
                # Check if it's time to send a chunk
                if elapsed >= (samples_per_chunk * 1000) // SAMPLE_RATE:
                    # Read audio samples
                    for i in range(samples_per_chunk):
                        # Read ADC and convert to 8-bit
                        sample = self.adc.read_u16() >> 8
                        self._buffer[self._buffer_index] = sample
                        self._buffer_index = (self._buffer_index + 1) % BUFFER_SIZE
                    
                    # Send chunk if channel is ready
                    if self._send_ready:
                        chunk = self._buffer[self._buffer_index:self._buffer_index + CHUNK_SIZE]
                        if len(chunk) < CHUNK_SIZE:
                            # Wrap around buffer
                            chunk.extend(self._buffer[:CHUNK_SIZE - len(chunk)])
                        
                        result = self._ble.l2cap_send(
                            self._l2cap_conn_handle,
                            self._l2cap_channel,
                            chunk
                        )
                        
                        if not result:
                            if dbg:
                                print("[!] Channel stalled")
                            self._send_ready = False
                    
                    last_time = current_time
                    self.led.toggle()  # Visual indicator of streaming
                    
                # Small delay to prevent busy waiting
                time.sleep_ms(1)
                
        except Exception as e:
            print(f"[-] Streaming error: {e}")

def demo():
    """Demo L2CAP audio streaming."""
    audio = BLEAudioL2CAP()
    
    try:
        print("[*] Starting audio stream...")
        audio.start_streaming()
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        audio._ble.active(False)

if __name__ == "__main__":
    demo() 
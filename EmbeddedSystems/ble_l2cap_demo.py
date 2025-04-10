import bluetooth
import struct
import time
from machine import Pin
from micropython import const

# Debug flag
dbg = 1

# IRQ Events for BLE and L2CAP
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)

# L2CAP Configuration
_L2CAP_PSM = const(0x70)  # Protocol/Service Multiplexer (must be even number)
_L2CAP_MTU = const(512)   # Maximum Transmission Unit

class BLEL2CAPDemo:
    def __init__(self, name="l2cap-demo"):
        """Initialize BLE and L2CAP communication."""
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Device info
        self._name = name
        self._connections = set()
        
        # L2CAP state
        self._l2cap_connected = False
        self._l2cap_conn_handle = None
        self._l2cap_channel = None
        self._send_ready = True
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        # Start as peripheral (listener)
        self._start_l2cap_server()
        self._advertise()
        
        if dbg:
            print("[*] L2CAP Server started")
            print(f"[*] PSM: 0x{_L2CAP_PSM:02X}")
            print(f"[*] MTU: {_L2CAP_MTU} bytes")

    def _irq(self, event, data):
        """Handle BLE and L2CAP events."""
        if event == _IRQ_CENTRAL_CONNECT:
            # Central device connected
            conn_handle, _, _ = data
            if dbg:
                print(f"[+] Connected: {conn_handle}")
            self._connections.add(conn_handle)
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            # Central device disconnected
            conn_handle, _, _ = data
            if dbg:
                print(f"[-] Disconnected: {conn_handle}")
            self._connections.remove(conn_handle)
            self._l2cap_connected = False
            self._l2cap_conn_handle = None
            self._l2cap_channel = None
            self._advertise()
            
        elif event == _IRQ_L2CAP_ACCEPT:
            # L2CAP connection request
            conn_handle, psm = data
            if dbg:
                print(f"[*] L2CAP Accept Request - Handle: {conn_handle}, PSM: {psm}")
            # Accept the connection (return 0 to accept, non-zero to reject)
            return 0
            
        elif event == _IRQ_L2CAP_CONNECT:
            # L2CAP channel established
            conn_handle, mtu, cid = data
            if dbg:
                print(f"[+] L2CAP Connected - Handle: {conn_handle}, MTU: {mtu}, CID: {cid}")
            self._l2cap_connected = True
            self._l2cap_conn_handle = conn_handle
            self._l2cap_channel = cid
            
        elif event == _IRQ_L2CAP_DISCONNECT:
            # L2CAP channel disconnected
            conn_handle, cid, status = data
            if dbg:
                print(f"[-] L2CAP Disconnected - Handle: {conn_handle}, CID: {cid}, Status: {status}")
            self._l2cap_connected = False
            self._l2cap_channel = None
            
        elif event == _IRQ_L2CAP_RECV:
            # Data received on L2CAP channel
            conn_handle, cid = data
            if dbg:
                print(f"[*] L2CAP Receive - Handle: {conn_handle}, CID: {cid}")
            
            # Read the data
            self._handle_l2cap_data()
            
        elif event == _IRQ_L2CAP_SEND_READY:
            # Channel ready for sending
            conn_handle, cid, status = data
            if dbg:
                print(f"[*] L2CAP Send Ready - Handle: {conn_handle}, CID: {cid}, Status: {status}")
            self._send_ready = True

    def _advertise(self, interval_us=100000):
        """Start advertising L2CAP service."""
        # Advertising payload
        payload = bytearray()
        # Add flags
        payload.extend(struct.pack('BB', 2, 0x01))  # Length, Type (Flags)
        payload.extend(b'\x06')  # General Discoverable, BR/EDR not supported
        # Add name
        name_bytes = self._name.encode()
        payload.extend(struct.pack('BB', len(name_bytes) + 1, 0x09))  # Length, Type (Name)
        payload.extend(name_bytes)
        
        self._ble.gap_advertise(interval_us, adv_data=payload)
        if dbg:
            print("[*] Advertising started")

    def _start_l2cap_server(self):
        """Start L2CAP server on specified PSM."""
        try:
            self._ble.l2cap_listen(_L2CAP_PSM, _L2CAP_MTU)
            if dbg:
                print(f"[+] L2CAP server listening on PSM: 0x{_L2CAP_PSM:02X}")
        except Exception as e:
            print(f"[-] Error starting L2CAP server: {e}")

    def send_data(self, data):
        """Send data over L2CAP channel."""
        if not self._l2cap_connected:
            if dbg:
                print("[-] Not connected")
            return False
            
        try:
            # Convert string to bytes if necessary
            if isinstance(data, str):
                data = data.encode()
                
            # Send data
            result = self._ble.l2cap_send(self._l2cap_conn_handle, self._l2cap_channel, data)
            if not result:
                if dbg:
                    print("[!] Channel stalled, waiting for send ready")
                self._send_ready = False
            return result
            
        except Exception as e:
            print(f"[-] Error sending data: {e}")
            return False

    def _handle_l2cap_data(self):
        """Handle received L2CAP data."""
        if not self._l2cap_connected:
            return
            
        try:
            # Create buffer for receiving
            buffer = bytearray(_L2CAP_MTU)
            # Read data into buffer
            bytes_read = self._ble.l2cap_recvinto(
                self._l2cap_conn_handle,
                self._l2cap_channel,
                buffer
            )
            
            if bytes_read > 0:
                # Process received data
                data = buffer[:bytes_read]
                if dbg:
                    print(f"[*] Received {bytes_read} bytes: {data}")
                
                # Echo data back (example handling)
                self.send_data(f"Echo: {data.decode()}")
                
        except Exception as e:
            print(f"[-] Error receiving data: {e}")

def demo():
    """Demo L2CAP communication."""
    l2cap = BLEL2CAPDemo()
    counter = 0
    
    try:
        while True:
            # Blink LED when connected
            if l2cap._l2cap_connected:
                l2cap.led.toggle()
                
                # Send periodic test data
                if l2cap._send_ready and counter % 10 == 0:
                    test_data = f"Test message {counter}"
                    if dbg:
                        print(f"[*] Sending: {test_data}")
                    l2cap.send_data(test_data)
            else:
                l2cap.led.off()
                
            counter += 1
            time.sleep_ms(100)
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        l2cap._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting L2CAP Demo")
    demo() 

'''
Usage Example:

# Create L2CAP instance
l2cap = BLEL2CAPDemo()

# Send data when connected
if l2cap._l2cap_connected:
    l2cap.send_data("Hello L2CAP!")

# Receive data is handled automatically via IRQ
'''
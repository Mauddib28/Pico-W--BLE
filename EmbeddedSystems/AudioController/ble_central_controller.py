import bluetooth
import struct
import time
from machine import Pin
from micropython import const

# Debug flag
dbg = 1

# Feature flags
#ENABLE_CLIENT_CONNECTION = const(1)  # Set to 0 to disable client connections
ENABLE_CLIENT_CONNECTION = True
# Device Name
_DEVICE_NAME = "BLE-Central"    # Device name for advertising

# IRQ Events
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)

# L2CAP Configuration
#_L2CAP_PSM_AUDIO = const(0x70)  # Audio channel
_L2CAP_PSM_CLIENT = const(0x72)  # Client control channel
#_L2CAP_MTU = const(512)

# Service UUIDs (16-bit) - For the Central Device
LED_SERVICE_UUID = const(0xA100)
AUDIO_SERVICE_UUID = const(0xA200)
# Service UUIDs (matching LED peripheral)
_LED_SERVICE_UUID = const(0xA100)
_RGB_CHAR_UUID = const(0xA101)
_STATUS_CHAR_UUID = const(0xA102)

# Client Service UUIDs
_CLIENT_SERVICE_UUID = const(0xA300)
_CLIENT_STATUS_CHAR_UUID = const(0xA301)
_CLIENT_CONTROL_CHAR_UUID = const(0xA302)

# L2CAP Configuration (matching audio peripheral)
_L2CAP_PSM_AUDIO = const(0x70)
_L2CAP_MTU = const(512)

class BLECentralController:
    def __init__(self, name="BLE-Central"):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._name = name
        
        # Device tracking
        self.led_device = None
        self.audio_device = None
        self.client_device = None
        
        # L2CAP channels
        self.audio_channel = None               # L2CAP State
        self.client_channel = None
        
        # Connection handles
        self._connections = {}  # addr -> conn_handle
        self._characteristics = {}  # addr -> characteristics
        
        # Status LED
        self.led = Pin("LED", Pin.OUT)
        
        # Scanning state
        self._scanning = False
        self._scan_results = set()

        # Client connection state
        self._client_connected = False
        self._client_handles = {}

        # Check for Client Connection Configuration
        if ENABLE_CLIENT_CONNECTION:
            self._register_client_service()
        
        if dbg:
            print("[*] BLE Central Controller initialized")
            if ENABLE_CLIENT_CONNECTION:
                print("[*] Client connections enabled")

    def _register_client_service(self):
        """Register service for client connections."""
        # Status characteristic
        status_char = (
            bluetooth.UUID(_CLIENT_STATUS_CHAR_UUID),
            bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
        )
        
        # Control characteristic
        control_char = (
            bluetooth.UUID(_CLIENT_CONTROL_CHAR_UUID),
            bluetooth.FLAG_WRITE,
        )
        
        # Client Service
        client_service = (
            bluetooth.UUID(_CLIENT_SERVICE_UUID),
            (status_char, control_char,),
        )
        
        # Register service
        ((self._handle_status, self._handle_control,),) = self._ble.gatts_register_services((client_service,))
        
        # Set initial values
        self._ble.gatts_write(self._handle_status, 'Ready'.encode())
        
        if dbg:
            print("[*] Client service registered")

    def _advertise(self):
        """Start advertising for client connections."""
        if not ENABLE_CLIENT_CONNECTION:
            return
            
        payload = bytearray()
        
        # Add flags
        payload.extend(struct.pack('BB', 2, 0x01))
        payload.extend(b'\x06')
        
        # Add name
        #name = "BLE-Controller"
        name_bytes = self._name.encode()
        payload.extend(struct.pack('BB', len(name_bytes) + 1, 0x09))
        payload.extend(name_bytes)
        
        # Add service UUID
        payload.extend(struct.pack('BBH', 3, 0x03, _CLIENT_SERVICE_UUID))
        
        # Start advertising
        self._ble.gap_advertise(100000, adv_data=payload)
        if dbg:
            print(f"[*] Advertising for client connections as '{self._name}'")

    def _update_client_status(self, status):
        """Update client status characteristic."""
        if ENABLE_CLIENT_CONNECTION:
            try:
                self._ble.gatts_write(self._handle_status, status.encode())
            except:
                pass

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr = bytes(addr)  # Convert to bytes
            
            if addr not in self._scan_results:
                name = None
                # Find device name
                i = 0
                while i < len(adv_data):
                    if i + 1 < len(adv_data):
                        field_length = adv_data[i]
                        field_type = adv_data[i + 1]
                        field_data = bytes(adv_data[i + 2:i + field_length + 1])  # Convert memoryview to bytes
                        
                        if field_type == 0x09:  # Complete Local Name
                            try:
                                name = field_data.decode()
                            except:
                                pass
                        elif field_type == 0x03:  # 16-bit Service UUIDs
                            for j in range(0, len(field_data), 2):
                                uuid = struct.unpack('<H', field_data[j:j+2])[0]
                                if uuid == _LED_SERVICE_UUID:
                                    print(f"[+] Found LED device: {addr.hex()}")
                                    self.led_device = addr
                                    self._ble.gap_connect(addr_type, addr)
                    i += adv_data[i] + 1
                    if dbg:
                        print(f"[*] Active connections: {len(self._connections)}")
                
                # Check for audio device by name
                if name == "BLE-I2S-Audio":
                    print(f"[+] Found Audio device: {addr.hex()}")
                    self.audio_device = addr
                    self._ble.gap_connect(addr_type, addr)
                
                self._scan_results.add(addr)
                
        elif event == _IRQ_SCAN_DONE:
            self._scanning = False
            if dbg:
                print("[*] Scan complete")
                
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            addr = bytes(addr)
            self._connections[addr] = conn_handle
            if dbg:
                print(f"[+] Connected to peripheral: {addr.hex()}")
                print(f"[*] Total connections: {len(self._connections)}")
            
            # If this is the LED device, discover services
            if addr == self.led_device:
                print("[*] Discovering LED services...")
                self._ble.gattc_discover_services(conn_handle)
            elif addr == self.audio_device:
                print("[*] Setting up L2CAP for audio...")
                self._ble.l2cap_connect(conn_handle, _L2CAP_PSM_AUDIO)
                
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            addr = bytes(addr)
            if addr in self._connections:
                del self._connections[addr]
            if dbg:
                print(f"[-] Peripheral disconnected: {addr.hex()}")
                print(f"[*] Remaining connections: {len(self._connections)}")
                
        elif event == _IRQ_L2CAP_ACCEPT:
            # Client connection request
            conn_handle, psm = data
            if psm == _L2CAP_PSM_CLIENT:
                if dbg:
                    print("[+] Client L2CAP connection request")
                return 0  # Accept
            return 1  # Reject other PSMs
            
        elif event == _IRQ_L2CAP_CONNECT:
            conn_handle, mtu, cid = data
            if conn_handle == self._connections.get(self.audio_device):
                self.audio_channel = cid
                if dbg:
                    print("[+] Audio L2CAP channel established")
            else:
                self.client_channel = cid
                if dbg:
                    print("[+] Client L2CAP channel established")
                    
        elif event == _IRQ_L2CAP_DISCONNECT:
            conn_handle, cid, status = data
            if cid == self.audio_channel:
                self.audio_channel = None
            elif cid == self.client_channel:
                self.client_channel = None
                
        elif event == _IRQ_L2CAP_RECV:
            conn_handle, cid = data
            if cid == self.client_channel:
                # Forward data from client to audio device
                self._handle_client_data()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == _LED_SERVICE_UUID:
                print("[+] Found LED service")
                # Discover characteristics
                self._ble.gattc_discover_characteristics(conn_handle, start_handle, end_handle)
                
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if uuid == _RGB_CHAR_UUID:
                addr = None
                # Find address for this connection handle
                for a, h in self._connections.items():
                    if h == conn_handle:
                        addr = a
                        break
                if addr:
                    if addr not in self._characteristics:
                        self._characteristics[addr] = {}
                    self._characteristics[addr]['rgb'] = value_handle
                    print("[+] Found RGB characteristic")

        ## Central IRQ Events
        # New client connection handling
        elif event == _IRQ_CENTRAL_CONNECT and ENABLE_CLIENT_CONNECTION:
            conn_handle, addr_type, addr = data
            self._client_connected = True
            self.client_device = bytes(addr)
            self._connections[addr] = conn_handle
            if dbg:
                print(f"[+] Client connected: {self.client_device.hex()}")
                print(f"[*] Total connetions: {len(self._connections)}")
            self._update_client_status("Connected")
            # Stop advertising when client connects
            self._ble.gap_advertise(None)  # Stop advertising
            if dbg:
                print("[*] Advertising stopped")
            
        elif event == _IRQ_CENTRAL_DISCONNECT and ENABLE_CLIENT_CONNECTION:
            conn_handle, addr_type, addr = data
            addr = bytes(addr)
            self._client_connected = False
            self.client_device = None
            if addr in self._connections:
                del self._connections[addr]
            if dbg:
                print(f"[-] Client disconnected: {addr.hex()}")
                print(f"[*] Remaining connections: {len(self._connections)}")
            self._update_client_status("Ready")
            # Restart advertising
            self._advertise()
            if dbg:
                print("[*] Advertising restarted")
            
        elif event == _IRQ_GATTS_WRITE and ENABLE_CLIENT_CONNECTION:
            conn_handle, attr_handle = data
            if attr_handle == self._handle_control:
                # Handle client control commands
                value = self._ble.gatts_read(self._handle_control)
                self._handle_client_command(value)

    def _handle_client_command(self, command):
        """Handle commands from client."""
        try:
            cmd = command.decode().strip()
            if dbg:
                print(f"[*] Client command: {cmd}")
            # Add command handling logic here
            self._update_client_status(f"Executed: {cmd}")
        except:
            self._update_client_status("Invalid command")

    def start(self):
        """Start the central controller."""
        print("[*] Starting scan for peripherals...")
        self._ble.gap_scan(2000, 30000, 30000)
        
        if ENABLE_CLIENT_CONNECTION and not self._client_connected:
            print("[*] Starting advertisement...")
            self._advertise()
        
        try:
            while True:
                #self.led.toggle()
                #time.sleep_ms(500)
                # Reconnect logic for peripherals
                if self.led_device and self.led_device not in self._connections:
                    self._ble.gap_connect(0, self.led_device)

                if self.audio_device and self.audio_device not in self._connections:
                    self._ble.gap_connect(0, self.audio_device)
            
                # Toggle LED and check if we need to re-advertise
                self.led.toggle()
                if ENABLE_CLIENT_CONNECTION and not self._client_connected:
                    self._advertise()  # Periodically try to advertise if no client

                if dbg and (len(self._connections) > 0):
                    print(f"[*] Active connections: {len(self._connections)}")
                    for addr in self._connections:
                        print(f"   - {addr.hex()}")

                time.sleep_ms(500)
                
        except KeyboardInterrupt:
            print("\n[-] Stopping controller")
            self._ble.active(False)

    def _handle_client_data(self):
        """Handle and forward client L2CAP data."""
        if not self.audio_channel:
            return
            
        try:
            # Read from client channel
            data = bytearray(_L2CAP_MTU)
            bytes_read = self._ble.l2cap_recvinto(
                self._connections[self.client_device],
                self.client_channel,
                data
            )
            
            if bytes_read > 0:
                # Forward to audio channel
                self._ble.l2cap_send(
                    self._connections[self.audio_device],
                    self.audio_channel,
                    data[:bytes_read]
                )
                if dbg:
                    print(f"[*] Forwarded {bytes_read} bytes")
                    
        except Exception as e:
            print(f"[-] Data forwarding error: {e}")

    def send_rgb(self, r, g, b):
        """Send RGB values to LED device."""
        if self.led_device and self.led_device in self._connections:
            try:
                # Format data as tab-separated string with newline (matching peripheral's expectation)
                rgb_data = f"{r}\t{g}\t{b}\n".encode()
                
                # Send to RGB characteristic
                rgb_handle = self._characteristics[self.led_device]['rgb']
                self._ble.gattc_write(self._connections[self.led_device], rgb_handle, rgb_data)
                if dbg:
                    print(f"[*] Sent RGB: {r}, {g}, {b}")
            except Exception as e:
                print(f"[-] RGB send error: {e}")

    def send_audio(self, audio_data):
        """Send audio data to audio device."""
        if self.audio_device and self.audio_channel:
            try:
                self._ble.l2cap_send(self._connections[self.audio_device], 
                                   self.audio_channel, 
                                   audio_data)
                if dbg:
                    print(f"[*] Sent {len(audio_data)} bytes of audio")
            except Exception as e:
                print(f"[-] Audio send error: {e}")

def demo():
    """Demo the central controller."""
    controller = BLECentralController()
    
    try:
        controller.start()
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        controller._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting BLE Central Controller")
    demo() 
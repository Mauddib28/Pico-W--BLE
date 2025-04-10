import bluetooth
import time
from micropython import const
from machine import Pin

# Debug flag
dbg = 1

# IRQ Events
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)

# Known Media Service UUIDs
MEDIA_SERVICE_UUID = bluetooth.UUID("A0000000-E8F2-537E-4F6C-D104768A1214")
PLAYBACK_CHAR_UUID = bluetooth.UUID("A0000001-E8F2-537E-4F6C-D104768A1214")
TRACK_INFO_CHAR_UUID = bluetooth.UUID("A0000002-E8F2-537E-4F6C-D104768A1214")
VOLUME_CHAR_UUID = bluetooth.UUID("A0000003-E8F2-537E-4F6C-D104768A1214")
STATUS_CHAR_UUID = bluetooth.UUID("A0000004-E8F2-537E-4F6C-D104768A1214")
METADATA_CHAR_UUID = bluetooth.UUID("A0000005-E8F2-537E-4F6C-D104768A1214")
POSITION_CHAR_UUID = bluetooth.UUID("A0000006-E8F2-537E-4F6C-D104768A1214")
DURATION_CHAR_UUID = bluetooth.UUID("A0000007-E8F2-537E-4F6C-D104768A1214")

class BLEMediaCentral:
    def __init__(self, max_devices=3):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Device tracking
        self.max_devices = max_devices
        self._devices = {}  # addr -> device info
        self._connections = {}  # addr -> conn_handle
        self._characteristics = {}  # addr -> char handles
        self._scan_results = set()
        
        # Status
        self._scanning = False
        self._connecting = False
        
        # LED for status
        self.led = Pin("LED", Pin.OUT)
        
        # Add metadata tracking
        self._metadata = {}  # addr -> metadata dict
        self._positions = {}  # addr -> playback position

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            
            # Check if device advertises our media service
            if MEDIA_SERVICE_UUID.to_bytes() in bytes(adv_data):
                addr = bytes(addr)  # Convert address to bytes
                if addr not in self._scan_results and len(self._devices) < self.max_devices:
                    name = self._decode_name(adv_data)
                    if dbg:
                        print(f"[*] Found media device: {name} ({addr})")
                    self._scan_results.add(addr)
                    self._devices[addr] = {"name": name, "services": {}}

        elif event == _IRQ_SCAN_DONE:
            self._scanning = False
            if dbg:
                print("[*] Scan complete")
            
            # Connect to discovered devices
            for addr in self._scan_results:
                if addr not in self._connections:
                    self._connect_to_device(addr)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            addr = bytes(addr)
            if dbg:
                print(f"[+] Connected: {self._devices[addr]['name']}")
            self._connections[addr] = conn_handle
            self._connecting = False
            
            # Discover services
            self._ble.gattc_discover_services(conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            addr = bytes(addr)
            if dbg:
                print(f"[-] Disconnected: {self._devices[addr]['name']}")
            if addr in self._connections:
                del self._connections[addr]
                del self._characteristics[addr]

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == MEDIA_SERVICE_UUID:
                addr = self._get_addr_from_conn_handle(conn_handle)
                self._devices[addr]["services"][uuid] = (start_handle, end_handle)
                if dbg:
                    print(f"[+] Found media service on {self._devices[addr]['name']}")

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            addr = self._get_addr_from_conn_handle(conn_handle)
            if MEDIA_SERVICE_UUID in self._devices[addr]["services"]:
                start, end = self._devices[addr]["services"][MEDIA_SERVICE_UUID]
                self._ble.gattc_discover_characteristics(conn_handle, start, end)

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            addr = self._get_addr_from_conn_handle(conn_handle)
            
            if addr not in self._characteristics:
                self._characteristics[addr] = {}
                
            self._characteristics[addr][uuid] = value_handle
            
            if dbg and uuid in [PLAYBACK_CHAR_UUID, TRACK_INFO_CHAR_UUID, 
                               VOLUME_CHAR_UUID, STATUS_CHAR_UUID,
                               METADATA_CHAR_UUID, POSITION_CHAR_UUID,
                               DURATION_CHAR_UUID]:
                print(f"[+] Found characteristic {uuid} on {self._devices[addr]['name']}")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            addr = self._get_addr_from_conn_handle(conn_handle)
            self._handle_notification(addr, value_handle, notify_data)

    def start_scan(self, duration_ms=5000):
        """Start scanning for media devices."""
        if not self._scanning:
            self._scanning = True
            self._scan_results.clear()
            self._ble.gap_scan(duration_ms, 30000, 30000)
            if dbg:
                print("[*] Scanning...")

    def _connect_to_device(self, addr):
        """Connect to a specific device."""
        if not self._connecting and len(self._connections) < self.max_devices:
            self._connecting = True
            self._ble.gap_connect(0, addr)
            if dbg:
                print(f"[*] Connecting to {self._devices[addr]['name']}...")

    def send_command(self, addr, command):
        """Send command to specific device."""
        if addr in self._connections and addr in self._characteristics:
            conn_handle = self._connections[addr]
            
            if PLAYBACK_CHAR_UUID in self._characteristics[addr]:
                value_handle = self._characteristics[addr][PLAYBACK_CHAR_UUID]
                self._ble.gattc_write(conn_handle, value_handle, command, 1)
                if dbg:
                    print(f"[*] Sent command to {self._devices[addr]['name']}")

    def set_volume(self, addr, volume):
        """Set volume for specific device (0-100)."""
        if addr in self._connections and addr in self._characteristics:
            conn_handle = self._connections[addr]
            
            if VOLUME_CHAR_UUID in self._characteristics[addr]:
                value_handle = self._characteristics[addr][VOLUME_CHAR_UUID]
                self._ble.gattc_write(conn_handle, value_handle, bytes([volume]), 1)
                if dbg:
                    print(f"[*] Set volume on {self._devices[addr]['name']}: {volume}%")

    # Helper methods
    def _decode_name(self, adv_data):
        """Decode device name from advertising data."""
        n = len(adv_data)
        i = 0
        while i < n:
            if adv_data[i + 1] == 0x09:
                return str(adv_data[i + 2:i + adv_data[i] + 1], "utf-8")
            i += adv_data[i] + 1
        return "Unknown"

    def _get_addr_from_conn_handle(self, conn_handle):
        """Get device address from connection handle."""
        for addr, handle in self._connections.items():
            if handle == conn_handle:
                return addr
        return None

    def get_metadata(self, addr):
        """Get current track metadata for a device."""
        if addr in self._connections and addr in self._characteristics:
            conn_handle = self._connections[addr]
            
            if METADATA_CHAR_UUID in self._characteristics[addr]:
                value_handle = self._characteristics[addr][METADATA_CHAR_UUID]
                self._ble.gattc_read(conn_handle, value_handle)
                # Note: Response will come via notification

    def get_position(self, addr):
        """Get current playback position for a device."""
        if addr in self._positions:
            return self._positions[addr]
        return None

    def get_volume(self, addr):
        """Get current volume level for a device."""
        if addr in self._connections and addr in self._characteristics:
            conn_handle = self._connections[addr]
            
            if VOLUME_CHAR_UUID in self._characteristics[addr]:
                value_handle = self._characteristics[addr][VOLUME_CHAR_UUID]
                self._ble.gattc_read(conn_handle, value_handle)
                # Note: Response will come via notification

    def get_track_info(self, addr):
        """Get comprehensive track info for a device."""
        if addr in self._metadata:
            return {
                "title": self._metadata[addr].get("title", "Unknown"),
                "artist": self._metadata[addr].get("artist", "Unknown"),
                "album": self._metadata[addr].get("album", "Unknown"),
                "genre": self._metadata[addr].get("genre", "Unknown"),
                "position": self._positions.get(addr, 0),
                "duration": self._metadata[addr].get("duration", 0),
                "volume": self._metadata[addr].get("volume", 0)
            }
        return None

    def _handle_notification(self, addr, value_handle, data):
        """Handle notifications from devices."""
        device_name = self._devices[addr]["name"]
        
        # Determine notification type based on characteristic
        for uuid, handle in self._characteristics[addr].items():
            if handle == value_handle:
                if uuid == STATUS_CHAR_UUID:
                    status = str(data, 'utf-8')
                    if dbg:
                        print(f"[*] Status update from {device_name}: {status}")
                
                elif uuid == TRACK_INFO_CHAR_UUID:
                    track = str(data, 'utf-8')
                    if dbg:
                        print(f"[*] Track update from {device_name}: {track}")
                
                elif uuid == METADATA_CHAR_UUID:
                    try:
                        # Expect metadata in JSON format
                        import json
                        metadata = json.loads(data.decode())
                        self._metadata[addr] = metadata
                        if dbg:
                            print(f"[*] Metadata update from {device_name}:")
                            print(f"    Title: {metadata.get('title', 'Unknown')}")
                            print(f"    Artist: {metadata.get('artist', 'Unknown')}")
                            print(f"    Album: {metadata.get('album', 'Unknown')}")
                    except:
                        print("[-] Error parsing metadata")
                
                elif uuid == POSITION_CHAR_UUID:
                    # Expect position in milliseconds
                    try:
                        import struct
                        position = struct.unpack('<I', data)[0]
                        self._positions[addr] = position
                        if dbg:
                            print(f"[*] Position update from {device_name}: {position}ms")
                    except:
                        print("[-] Error parsing position")
                
                elif uuid == VOLUME_CHAR_UUID:
                    volume = data[0]
                    if addr in self._metadata:
                        self._metadata[addr]['volume'] = volume
                    if dbg:
                        print(f"[*] Volume update from {device_name}: {volume}%")

def demo():
    central = BLEMediaCentral(max_devices=3)
    
    try:
        while True:
            # Scan for devices periodically if not at max connections
            if len(central._connections) < central.max_devices:
                central.start_scan()
            
            # Query metadata from connected devices
            for addr in central._connections:
                central.get_metadata(addr)
                central.get_volume(addr)
                
                # Print current track info
                track_info = central.get_track_info(addr)
                if track_info:
                    device_name = central._devices[addr]["name"]
                    print(f"\nNow playing on {device_name}:")
                    print(f"Title: {track_info['title']}")
                    print(f"Artist: {track_info['artist']}")
                    print(f"Album: {track_info['album']}")
                    print(f"Genre: {track_info['genre']}")
                    print(f"Position: {track_info['position']}ms")
                    print(f"Duration: {track_info['duration']}ms")
                    print(f"Volume: {track_info['volume']}%")
            
            # Blink LED if we have any connections
            if central._connections:
                central.led.toggle()
            else:
                central.led.off()
                
            time.sleep_ms(2000)  # Query every 2 seconds
            
    except KeyboardInterrupt:
        print("\n[-] Stopping central device")
        central._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting BLE Media Central")
    demo() 

'''
Usage Example:

central = BLEMediaCentral()
central.start_scan()

# After devices are connected...
for addr in central._connections:
    # Get current track info
    info = central.get_track_info(addr)
    if info:
        print(f"Now playing: {info['title']} by {info['artist']}")
        print(f"From album: {info['album']}")
        print(f"Volume: {info['volume']}%")
'''
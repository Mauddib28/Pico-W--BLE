import bluetooth
from machine import Pin
import struct
from micropython import const
from ble_advertising import advertising_payload
import time

# IRQ Event Constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_READ_REQUEST = const(4)

# Flag Constants for Read Characteristics
_FLAG_READ = const(0x0002)
_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)

# Service UUID
_READ_DEMO_UUID = bluetooth.UUID("A5A5A5A5-0000-1111-2222-333344445555")

# Characteristic UUIDs with different read properties
_BASIC_READ = (
    bluetooth.UUID("A5A5A5A5-0001-1111-2222-333344445555"),
    _FLAG_READ,
)

_ENCRYPTED_READ = (
    bluetooth.UUID("A5A5A5A5-0002-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_ENCRYPTED,
)

_AUTHENTICATED_READ = (
    bluetooth.UUID("A5A5A5A5-0003-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_AUTHENTICATED,
)

_AUTHORIZED_READ = (
    bluetooth.UUID("A5A5A5A5-0004-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_AUTHORIZED,
)

# Combine all characteristics into one service
_READ_SERVICE = (
    _READ_DEMO_UUID,
    (_BASIC_READ, _ENCRYPTED_READ, _AUTHENTICATED_READ, _AUTHORIZED_READ),
)

class BLEReadDemo:
    def __init__(self, ble, name="read-demo"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Register service and get handles
        ((self._handle_basic, 
          self._handle_encrypted,
          self._handle_authenticated,
          self._handle_authorized),) = self._ble.gatts_register_services((_READ_SERVICE,))
        
        # Initialize characteristic values
        self._ble.gatts_write(self._handle_basic, b'Basic Read Value')
        self._ble.gatts_write(self._handle_encrypted, b'Encrypted Read Value')
        self._ble.gatts_write(self._handle_authenticated, b'Authenticated Read Value')
        self._ble.gatts_write(self._handle_authorized, b'Authorized Read Value')
        
        self._connections = set()

        self.adv_test = 0
        if self.adv_test != 0:
            self._payload = advertising_payload(name=name, services=[_READ_DEMO_UUID])
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("Connected:", conn_handle)
            self._connections.add(conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected:", conn_handle)
            self._connections.remove(conn_handle)
            self._advertise()

        elif event == _IRQ_GATTS_READ_REQUEST:
            conn_handle, attr_handle = data
            print(f"Read request - handle: {attr_handle}")
            
            # Demonstrate different read responses based on characteristic type
            if attr_handle == self._handle_basic:
                print("Basic read accessed")
                return # Allow normal read
                
            elif attr_handle == self._handle_encrypted:
                # In a real implementation, check encryption status
                print("Encrypted read accessed")
                return
                
            elif attr_handle == self._handle_authenticated:
                # In a real implementation, check authentication
                print("Authenticated read accessed")
                return
                
            elif attr_handle == self._handle_authorized:
                # In a real implementation, check authorization
                print("Authorized read accessed")
                return

    def _advertise(self, interval_us=500000):
        # Main advertising data - just UUID
        adv_data = advertising_payload(services=[_READ_DEMO_UUID])
        
        # Additional data in scan response
        resp_data = advertising_payload(name="read-demo")

        # Remove the appearance data from the Advertisement Payload
        appearance=0        # Remove appearance
        
        self._ble.gap_advertise(interval_us, adv_data=adv_data, resp_data=resp_data)

def demo():
    ble = bluetooth.BLE()
    read_demo = BLEReadDemo(ble)
    
    led = Pin("LED", Pin.OUT)
    counter = 0
    
    while True:
        if counter % 10 == 0:
            led.toggle()
            
            # Update basic read value with counter
            read_demo._ble.gatts_write(read_demo._handle_basic, 
                                     f"Basic Read: {counter}".encode())
            
        time.sleep_ms(100)
        counter += 1

if __name__ == "__main__":
    print("Starting BLE Read Characteristics Demo")
    demo() 
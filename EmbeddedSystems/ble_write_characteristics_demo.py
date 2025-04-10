import bluetooth
from machine import Pin
import struct
from micropython import const
from ble_advertising import advertising_payload
import time

# IRQ Event Constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# Flag Constants for Write Characteristics
_FLAG_WRITE = const(0x0008)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)
_FLAG_AUTHENTICATED_SIGNED_WRITE = const(0x0040)
_FLAG_READ = const(0x0002)  # For result characteristic

# Service UUID
_WRITE_DEMO_UUID = bluetooth.UUID("BEEF0000-1337-4242-9999-222222222222")

# Write Characteristics
_BASIC_WRITE = (
    bluetooth.UUID("BEEF0001-1337-4242-9999-222222222222"),
    _FLAG_WRITE,
)

_WRITE_NO_RESPONSE = (
    bluetooth.UUID("BEEF0002-1337-4242-9999-222222222222"),
    _FLAG_WRITE_NO_RESPONSE,
)

_ENCRYPTED_WRITE = (
    bluetooth.UUID("BEEF0003-1337-4242-9999-222222222222"),
    _FLAG_WRITE | _FLAG_WRITE_ENCRYPTED,
)

_AUTHENTICATED_WRITE = (
    bluetooth.UUID("BEEF0004-1337-4242-9999-222222222222"),
    _FLAG_WRITE | _FLAG_WRITE_AUTHENTICATED,
)

_AUTHORIZED_WRITE = (
    bluetooth.UUID("BEEF0005-1337-4242-9999-222222222222"),
    _FLAG_WRITE | _FLAG_WRITE_AUTHORIZED,
)

_SIGNED_WRITE = (
    bluetooth.UUID("BEEF0006-1337-4242-9999-222222222222"),
    _FLAG_AUTHENTICATED_SIGNED_WRITE,
)

# Result Characteristic (readable)
_WRITE_RESULT = (
    bluetooth.UUID("BEEF0007-1337-4242-9999-222222222222"),
    _FLAG_READ,
)

# Combine all characteristics into one service
_WRITE_SERVICE = (
    _WRITE_DEMO_UUID,
    (_BASIC_WRITE, _WRITE_NO_RESPONSE, _ENCRYPTED_WRITE, 
     _AUTHENTICATED_WRITE, _AUTHORIZED_WRITE, _SIGNED_WRITE,
     _WRITE_RESULT),
)

class BLEWriteDemo:
    def __init__(self, ble, name="write-demo"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Register service and get handles
        ((self._handle_basic,
          self._handle_no_response,
          self._handle_encrypted,
          self._handle_authenticated,
          self._handle_authorized,
          self._handle_signed,
          self._handle_result),) = self._ble.gatts_register_services((_WRITE_SERVICE,))
        
        # Initialize result characteristic
        self._ble.gatts_write(self._handle_result, b'No writes yet')
        
        self._connections = set()
        
        # Split advertising data to stay within size limits
        self.adv_test = 0
        if self.adv_test != 0:
            self._payload = advertising_payload(name=name, services=[_WRITE_DEMO_UUID])
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

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            
            # Get the written value
            value = self._ble.gatts_read(attr_handle)
            result = ""
            
            # Process write based on characteristic
            if attr_handle == self._handle_basic:
                result = f"Basic write: {value}"
                
            elif attr_handle == self._handle_no_response:
                result = f"Write no response: {value}"
                
            elif attr_handle == self._handle_encrypted:
                # In real implementation, verify encryption
                result = f"Encrypted write: {value}"
                
            elif attr_handle == self._handle_authenticated:
                # In real implementation, verify authentication
                result = f"Authenticated write: {value}"
                
            elif attr_handle == self._handle_authorized:
                # In real implementation, verify authorization
                result = f"Authorized write: {value}"
                
            elif attr_handle == self._handle_signed:
                # In real implementation, verify signature
                result = f"Signed write: {value}"
            
            # Update result characteristic
            if result:
                print(result)
                self._ble.gatts_write(self._handle_result, result.encode())

    def _advertise(self, interval_us=500000):
        # Main advertising data - just UUID
        adv_data = advertising_payload(services=[_WRITE_DEMO_UUID])
        
        # Additional data in scan response
        resp_data = advertising_payload(name="write-demo")

        # Remove the appearance data from the Advertisement Payload
        appearance=0        # Remove appearance
        
        self._ble.gap_advertise(interval_us, adv_data=adv_data, resp_data=resp_data)

def demo():
    ble = bluetooth.BLE()
    write_demo = BLEWriteDemo(ble)
    
    led = Pin("LED", Pin.OUT)
    
    while True:
        led.toggle()
        time.sleep_ms(500)

if __name__ == "__main__":
    print("Starting BLE Write Characteristics Demo")
    demo() 
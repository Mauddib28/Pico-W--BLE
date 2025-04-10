import bluetooth
from machine import Pin
import struct
from micropython import const
from ble_advertising import advertising_payload
import time

# IRQ Event Constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

# Flag Constants for Notify/Indicate Characteristics
_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)
_FLAG_NOTIFY_ENCRYPTED = const(0x1010)  # Combined with encryption
_FLAG_NOTIFY_AUTHENTICATED = const(0x2010)  # Combined with authentication
_FLAG_NOTIFY_AUTHORIZED = const(0x4010)  # Combined with authorization

# Service UUID
_NOTIFY_DEMO_UUID = bluetooth.UUID("DEAD0000-1337-4242-9999-222222222222")

# Notification Characteristics
_BASIC_NOTIFY = (
    bluetooth.UUID("DEAD0001-1337-4242-9999-222222222222"),
    _FLAG_READ | _FLAG_NOTIFY,
)

_ENCRYPTED_NOTIFY = (
    bluetooth.UUID("DEAD0002-1337-4242-9999-222222222222"),
    _FLAG_READ | _FLAG_NOTIFY_ENCRYPTED,
)

_AUTHENTICATED_NOTIFY = (
    bluetooth.UUID("DEAD0003-1337-4242-9999-222222222222"),
    _FLAG_READ | _FLAG_NOTIFY_AUTHENTICATED,
)

_AUTHORIZED_NOTIFY = (
    bluetooth.UUID("DEAD0004-1337-4242-9999-222222222222"),
    _FLAG_READ | _FLAG_NOTIFY_AUTHORIZED,
)

_BASIC_INDICATE = (
    bluetooth.UUID("DEAD0005-1337-4242-9999-222222222222"),
    _FLAG_READ | _FLAG_INDICATE,
)

# Status Characteristic (readable)
_NOTIFY_STATUS = (
    bluetooth.UUID("DEAD0006-1337-4242-9999-222222222222"),
    _FLAG_READ,
)

# Combine all characteristics into one service
_NOTIFY_SERVICE = (
    _NOTIFY_DEMO_UUID,
    (_BASIC_NOTIFY, _ENCRYPTED_NOTIFY, _AUTHENTICATED_NOTIFY, 
     _AUTHORIZED_NOTIFY, _BASIC_INDICATE, _NOTIFY_STATUS),
)

class BLENotifyDemo:
    def __init__(self, ble, name="notify-demo"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Register service and get handles
        ((self._handle_basic_notify,
          self._handle_encrypted_notify,
          self._handle_authenticated_notify,
          self._handle_authorized_notify,
          self._handle_indicate,
          self._handle_status),) = self._ble.gatts_register_services((_NOTIFY_SERVICE,))
        
        self._connections = set()
        self._indicate_pending = False
        
        # Split advertising to stay within size limits
        adv_data = advertising_payload(services=[_NOTIFY_DEMO_UUID])
        resp_data = advertising_payload(name="notify-demo")
        self._ble.gap_advertise(500000, adv_data=adv_data, resp_data=resp_data)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("[+] Connected:", conn_handle)
            self._connections.add(conn_handle)
            self._update_status(f"Connected: {conn_handle}")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("[-] Disconnected:", conn_handle)
            self._connections.remove(conn_handle)
            self._indicate_pending = False
            self._advertise()
            self._update_status("Disconnected")

        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data
            print(f"[*] Indication {'acknowledged' if status == 0 else 'failed'}")
            self._indicate_pending = False

    def _update_status(self, status):
        print(f"[*] Status: {status}")
        self._ble.gatts_write(self._handle_status, status.encode())

    def notify_all(self, data, security_level=0):
        """
        Send notification with different security levels:
        0 = Basic
        1 = Encrypted
        2 = Authenticated
        3 = Authorized
        """
        if not self._connections:
            return
        
        handles = [
            self._handle_basic_notify,
            self._handle_encrypted_notify,
            self._handle_authenticated_notify,
            self._handle_authorized_notify
        ]
        
        if security_level < len(handles):
            for conn_handle in self._connections:
                self._ble.gatts_notify(conn_handle, handles[security_level], data)
                self._update_status(f"Notification sent (level {security_level})")

    def indicate(self, data):
        """Send indication and wait for acknowledgment"""
        if self._indicate_pending or not self._connections:
            return False
        
        for conn_handle in self._connections:
            self._indicate_pending = True
            self._ble.gatts_indicate(conn_handle, self._handle_indicate, data)
            self._update_status("Indication sent")
        return True

def demo():
    ble = bluetooth.BLE()
    notify_demo = BLENotifyDemo(ble)
    
    led = Pin("LED", Pin.OUT)
    counter = 0
    
    while True:
        if notify_demo._connections:
            led.on()
            
            # Rotate through different notification types
            security_level = counter % 4
            notify_demo.notify_all(f"Notify {counter}".encode(), security_level)
            
            # Send indication every 5 counts
            if counter % 5 == 0:
                notify_demo.indicate(f"Indicate {counter}".encode())
            
            counter += 1
            time.sleep_ms(1000)
        else:
            led.off()
            time.sleep_ms(100)

if __name__ == "__main__":
    print("[*] Starting BLE Notification Demo")
    demo() 
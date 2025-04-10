import bluetooth
import struct
import time
from machine import Pin
from micropython import const

# Debug flag
dbg = 1

# IRQ Events
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
_IRQ_PASSKEY_ACTION = const(31)

# Passkey actions
_PASSKEY_ACTION_NONE = const(0)
_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISPLAY = const(3)
_PASSKEY_ACTION_NUMERIC_COMPARISON = const(4)

# Security levels
_SECURITY_MODE1_LEVEL1 = const(0)  # No security
_SECURITY_MODE1_LEVEL2 = const(1)  # Unauthenticated pairing with encryption
_SECURITY_MODE1_LEVEL3 = const(2)  # Authenticated pairing with encryption
_SECURITY_MODE1_LEVEL4 = const(3)  # Authenticated LE Secure Connections pairing with encryption

class BLESecureDevice:
    def __init__(self, name="secure-device"):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._name = name
        self._connections = set()
        self.led = Pin("LED", Pin.OUT)
        
        # Security-related state
        self._paired = False
        self._encrypted = False
        self._bonded = False
        self._secrets = {}  # Store bonding keys
        
        # Configure security
        self._configure_security()
        # Start advertising
        self._advertise()
        
        if dbg:
            print("[*] Secure BLE device initialized")

    def _configure_security(self):
        """Configure security parameters."""
        self._ble.config(
            bond=True,  # Enable bonding
            mitm=True,  # Enable MITM protection
            io=_PASSKEY_ACTION_DISPLAY,  # Use display for passkey
            le_secure=True,  # Enable LE Secure Connections
            security_mode=_SECURITY_MODE1_LEVEL3,  # Require authenticated pairing
        )
        if dbg:
            print("[*] Security configured")

    def _irq(self, event, data):
        """Handle BLE events."""
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            if dbg:
                print(f"[+] Connected: {bytes(addr)}")
            self._connections.add(conn_handle)
            # Initiate pairing
            self._ble.gap_pair(conn_handle)
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            if dbg:
                print(f"[-] Disconnected: {bytes(addr)}")
            self._connections.remove(conn_handle)
            self._paired = False
            self._encrypted = False
            self._advertise()
            
        elif event == _IRQ_ENCRYPTION_UPDATE:
            # Encryption has been enabled or disabled
            conn_handle, encrypted, authenticated, bonded, key_size = data
            if dbg:
                print(f"[*] Encryption update:")
                print(f"    Encrypted: {encrypted}")
                print(f"    Authenticated: {authenticated}")
                print(f"    Bonded: {bonded}")
                print(f"    Key Size: {key_size}")
            
            self._encrypted = encrypted
            self._bonded = bonded
            
        elif event == _IRQ_GET_SECRET:
            # Request for stored bonding keys
            sec_type, index, key = data
            if dbg:
                print(f"[*] Get secret - Type: {sec_type}, Index: {index}")
            
            if sec_type in self._secrets and index in self._secrets[sec_type]:
                return self._secrets[sec_type][index]
            return None
            
        elif event == _IRQ_SET_SECRET:
            # Store bonding keys
            sec_type, index, data = data
            if dbg:
                print(f"[*] Set secret - Type: {sec_type}, Index: {index}")
            
            if sec_type not in self._secrets:
                self._secrets[sec_type] = {}
            self._secrets[sec_type][index] = data
            return True
            
        elif event == _IRQ_PASSKEY_ACTION:
            conn_handle, action, passkey = data
            if dbg:
                print(f"[*] Passkey action: {action}")
            
            if action == _PASSKEY_ACTION_DISPLAY:
                # Generate and display passkey
                if passkey is None:
                    import random
                    passkey = random.randint(0, 999999)
                print(f"[*] Passkey: {passkey:06d}")
                self._ble.gap_passkey(conn_handle, action, passkey)
                
            elif action == _PASSKEY_ACTION_INPUT:
                # Request passkey input
                print("[?] Enter passkey displayed on peer device:")
                passkey = int(input())
                self._ble.gap_passkey(conn_handle, action, passkey)
                
            elif action == _PASSKEY_ACTION_NUMERIC_COMPARISON:
                # Request numeric comparison
                print(f"[?] Compare: {passkey:06d}")
                print("    Accept? (y/n):")
                if input().strip().lower() == 'y':
                    self._ble.gap_passkey(conn_handle, action, 1)
                else:
                    self._ble.gap_passkey(conn_handle, action, 0)

    def _advertise(self, interval_us=100000):
        """Start advertising with security flags."""
        payload = bytearray()
        # Add flags
        payload.extend(struct.pack('BB', 2, 0x01))
        payload.extend(b'\x06')  # General discoverable, BR/EDR not supported
        
        # Add name
        name_bytes = self._name.encode()
        payload.extend(struct.pack('BB', len(name_bytes) + 1, 0x09))
        payload.extend(name_bytes)
        
        # Add security flags
        payload.extend(struct.pack('BB', 3, 0x01))
        payload.extend(b'\x04\x18\x04')  # BR/EDR Not Supported, LE Secure Connections
        
        self._ble.gap_advertise(interval_us, adv_data=payload)
        if dbg:
            print("[*] Advertising started")

    def is_paired(self):
        """Check if device is paired."""
        return self._paired

    def is_encrypted(self):
        """Check if connection is encrypted."""
        return self._encrypted

    def is_bonded(self):
        """Check if device is bonded."""
        return self._bonded

def demo():
    """Demo secure BLE device."""
    secure_dev = BLESecureDevice()
    
    try:
        while True:
            # Blink LED based on security state
            if secure_dev._connections:
                if secure_dev.is_encrypted():
                    # Fast blink for encrypted connection
                    secure_dev.led.on()
                    time.sleep_ms(100)
                    secure_dev.led.off()
                    time.sleep_ms(100)
                else:
                    # Slow blink for unencrypted connection
                    secure_dev.led.on()
                    time.sleep_ms(500)
                    secure_dev.led.off()
                    time.sleep_ms(500)
            else:
                secure_dev.led.off()
                time.sleep_ms(1000)
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        secure_dev._ble.active(False)

if __name__ == "__main__":
    print("[*] Starting Secure BLE Demo")
    demo() 

'''
Usage Example:

# Create secure device
secure_dev = BLESecureDevice()

# Check security status
if secure_dev.is_paired():
    print("Device is paired")
if secure_dev.is_encrypted():
    print("Connection is encrypted")
if secure_dev.is_bonded():
    print("Device is bonded")
'''
# PiCockpit.com
#	- URL:		https://picockpit.com/raspberry-pi/everything-about-bluetooth-on-the-raspberry-pi-pico-w/
## Note: This code functions an an RX/TX channel between two devices

# Example Micropython github for bonding
#   - URL:      https://github.com/micropython/micropython/blob/master/examples/bluetooth/ble_bonding_peripheral.py

###
# Edited by:		Paul Wortman	-	2024/12/28
# Edited by:        <insert name>   -   <date; cool way>
###

## Alteration History
# Added print statements for tracking interaction
# Added additional IRQ events + resource URL
# Converted for passing an RGB array to a characteristic, to then drive LEDs

## TODO:
#	[x] Additional functions for BLE
#	[x] Have "backside" operations from BLE Characteristics
#	[x] Add UUIDs
#	[ ] Make changes to the GAP service
#	[x] Tie in functionality to the added Read and Write Services + associated characteristics
#	[ ] Figure out why UART write does not have additional types/variation when writing with nrfConnect for UART RX
#       - Note: Might have to do with the R/W variable internal to the Characteristic?
#       - Assumption is that it must depend on how the Characteristic presents itself (e.g. property, UUID); pre-configured/known?
#   [x] Add debugging for important IRQ Events
#       [ ] Add encryption/secret IRQ Event debugging
#   [ ] Test bonding with this server

## General Notes:
# In the current version [ 2023/09/21 ] it appears that the UART RX service characteristic is just writing to the local Characteristic(/Descriptor?)'s variable-soemthing (???)
#   - Goal:     Get Characteristics to interact with a local variable (can provide values or output)
#   - Found:    Each Characteristic has its own R/W variable belonging to that characteristic (?? Needs further testing)
# Figured out how to point to the correct spots for R/W of GATT Characteristics [ 2023/09/22 ]
# Confirmed the R/W actions with variables all work as epxected
# Created flag to disable/enable notification sending by the server; N.B.: Potential for distributed distilation of signals

import bluetooth
import random
import struct
import time
from machine import Pin, PWM
from ble_advertising import advertising_payload

from micropython import const

# Debugging
dbg = 0
demo_notify_flag = 0        # Note: Use this flag to enable/disable usage of the gattc_notify() function call via internal send() Class function

#####
#
# Configuration of Variables, Constants, and Flags
#
#####

# Setting constants for the IRQ (i.e. response aspects) with GATT
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
# Note: The above come from the micropython bluetooth library documentation
#	- URL:		http://docs.micropython.org/en/latest/library/bluetooth.html
_IRQ_PASSKEY_ACTION = const(31)     # Note: Extrapolated from the above documentation

## Response codes for _IRQ_GATTS_READ_REQUEST event
_GATTS_NO_ERROR = const(0x00)
_GATTS_ERROR_READ_NOT_PERMITTED = const(0x02)
_GATTS_ERROR_WRITE_NOT_PERMITTED = const(0x03)
_GATTS_ERROR_INSUFFICIENT_AUTHENTICATION = const(0x05)
_GATTS_ERROR_INSUFFICIENT_AUTHORIZATION = const(0x08)
_GATTS_ERROR_INSUFFICIENT_ENCRYPTION = const(0x0f)

# Configuring the Flags for use with Bluetooth LE
_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)
# For eventual use for encrypted communications
_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)
_FLAG_AUTHENTICATED_SIGNED_WRITE = const(0x0040)
_FLAG_AUX_WRITE = const(0x0100)

# LED Constants; Uses a 330 Ohm resistor -[ Orange - Orange - Brown - Gold || Orange - Orange - Black - Black - Gold ]-
TEST__YELLOW_WIRE = 13
TEST__ORANGE_WIRE = 12
TEST__WHITE_WIRE = 11
LED_SWITCH = False  #True
LED_PWM = True
TEST_FREQ = 1000

## Configure the LED Pins
if not LED_PWM:
    ## LED Objects
    # Basic On/Off LEDs
    oj_led = Pin(TEST__ORANGE_WIRE, Pin.OUT)
    oj_led.off()
    yl_led = Pin(TEST__YELLOW_WIRE, Pin.OUT)
    yl_led.off()
    wt_led = Pin(TEST__WHITE_WIRE, Pin.OUT)
    wt_led.off()
else:
    # PWM LEDs
    oj_led = Pin(TEST__ORANGE_WIRE)
    oj_pwm = PWM(oj_led)
    oj_pwm.freq(TEST_FREQ)
    yt_led = Pin(TEST__YELLOW_WIRE)
    yl_pwm = PWM(yt_led)
    yl_pwm.freq(TEST_FREQ)
    wt_led = Pin(TEST__WHITE_WIRE)
    wt_pwm = PWM(wt_led)
    wt_pwm.freq(TEST_FREQ)
# PWM Timing Variables
fade_interval = 10
max_pwm_brightness = 255
min_pwm_brightness = 0
# Configur PWM properties (if needed)
#analogWriteRange(65535)
#analogWriteResolution(16)
duty_step = 129     # Step size for chaning the duty cycle
pwm_duty_step = 257     # Step size of the PWM for the LEDs

#####
#
# Universally Unique Identification (UUID) Section
#
# Purpose:  Configure, identify, and packing any BLE GATT Services, Characteristics, or Descriptors for the GATT Server; which is configured later on in the code
#
#####

## Note: All the UUIDs below are the same; because they are all part of the same service (???)
# Setting the UUID and BLE Flags for the larger UART Service/Characteristic
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
# Setting the UUID and BLE Flags for the UART TX Service/Characteristic
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
# Setting the UUID and BLE Flags for the UART RX Service/Characteristic
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
# Configuring the actual BLE GATT UART Service
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

## Scatch Space for Adding a New Service and Characteristic Definitions
# Setting the UUID for a Read Service
_READ_UUID = bluetooth.UUID("13372EAD-0000-1111-2222-333344445555")
# Setting the UUID and BLE Flags for the First Charateristic of this Service
_READ_COUNTER = (
    bluetooth.UUID("13372EAD-0001-1111-2222-333344445555"),
    _FLAG_READ,
    )
# Note: The purpoe of the above function is to Read from an every growing counter
# Setting the UUID and BLE Flags for the Second Characteristic of this Service
_READ_VARIABLE = (
    bluetooth.UUID("13372EAD-0002-1111-2222-333344445555"),
    _FLAG_READ,
    )
# Note: The purpose of the above function is to hold a value that can be updated via other means and read (e.g. result of an operaiton)
# Setting the UUID and BLE Flags for a Read that is Encrypted
_READ_ENCRYPTED = (
    bluetooth.UUID("13372EAD-0003-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_ENCRYPTED,
    )
# Setting the UUID and BLE Flags for a Read that is Authenticated
_READ_AUTHENTICATED = (
    bluetooth.UUID("13372EAD-0004-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_AUTHENTICATED,
    )
# Seeting the UUID and BLE Flags for a Read that is Authorized
_READ_AUTHORIZED = (
    bluetooth.UUID("13372EAD-0005-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_READ_AUTHORIZED,
    )
# Setting the UUID for a Write Service
_WRITE_UUID = bluetooth.UUID("0003217E-0000-1111-2222-333344445555")
# Setting the UUID and BLE Flags for the First Characteristic of this Serivce
_WRITE_GENERAL = (
    bluetooth.UUID("0003217E-0001-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
    )
# Note: The purpose of the above function is to take any Write action; WRITE + NO RESP
# Setting the UUID and BLE Flags for the Second Characteristic of this Service
_WRITE_VARIABLE = (
    bluetooth.UUID("0003217E-0002-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
    )
# Note: The purpose of the above function is to take a given Write action; writing the provided information to the value read from the Second Characteristic of the Read Service
# Setting the UUID and BLE Flags for a Write that is Encrypted
_WRITE_ENCRYPTED = (
    bluetooth.UUID("0003217E-0003-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_WRITE_ENCRYPTED,
    )
# Setting the UUID and BLE Flags for a Write that is Authenticated
_WRITE_AUTHENTICATED = (
    bluetooth.UUID("0003217E-0004-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_WRITE_AUTHENTICATED,
    )
# Setting the UUID and BLE Flags for a Write that is Authorized
_WRITE_AUTHORIZED = (
    bluetooth.UUID("0003217E-0005-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_WRITE_AUTHORIZED,
    )
# Setting the UUID and BLE Flags for a Write that is Authenticated and Signed
_WRITE_AUTHENTICATED_SIGNED = (
    bluetooth.UUID("0003217E-0006-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_AUTHENTICATED_SIGNED_WRITE,
    )
# Setting the UUID and BLE Flags for a Write that is Aux[iliary]
_WRITE_AUX = (
    bluetooth.UUID("0003217E-0007-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_AUX_WRITE,
    )
## TODO: Create a No Reponse Version of the Above
# Setting the UUID and BLE Flags for the First Characteristic of this Serivce
_WRITE_RESPONSE_GENERAL = (
    bluetooth.UUID("0003217E-0008-1111-2222-333344445555"),
    _FLAG_WRITE,
    )
# Note: The purpose of the above function is to take any Write action; WRITE + NO RESP
# Setting the UUID and BLE Flags for the Second Characteristic of this Service
_WRITE_RESPONSE_VARIABLE = (
    bluetooth.UUID("0003217E-0009-1111-2222-333344445555"),
    _FLAG_WRITE,
    )
# Note: The purpose of the above function is to take a given Write action; writing the provided information to the value read from the Second Characteristic of the Read Service
# Setting the UUID and BLE Flags for a Write that is Encrypted
_WRITE_NO_RESPONSE_ENCRYPTED = (
    bluetooth.UUID("0003217E-000A-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_WRITE_ENCRYPTED,
    )
# Setting the UUID and BLE Flags for a Write that is Authenticated
_WRITE_NO_RESPONSE_AUTHENTICATED = (
    bluetooth.UUID("0003217E-000B-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_WRITE_AUTHENTICATED,
    )
# Setting the UUID and BLE Flags for a Write that is Authorized
_WRITE_NO_RESPONSE_AUTHORIZED = (
    bluetooth.UUID("0003217E-000C-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_WRITE_AUTHORIZED,
    )
# Setting the UUID and BLE Flags for a Write that is Authenticated and Signed
_WRITE_NO_RESPONSE_AUTHENTICATED_SIGNED = (
    bluetooth.UUID("0003217E-000D-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_AUTHENTICATED_SIGNED_WRITE,
    )
# Setting the UUID and BLE Flags for a Write that is Aux[iliary]
_WRITE_NO_RESPONSE_AUX = (
    bluetooth.UUID("0003217E-000E-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_AUX_WRITE,
    )

# Setting the UUID for an Audio Service; NOTE: One of the two commented out UUIDs caused an error of "Error 1 (0x1): GATT INVALID HANDLE"
#_RGB_UUID = bluetooth.UUID("DEADBEEF-CAFE-0F04-1337-DEADCAFEBEEF")
_RGB_UUID = bluetooth.UUID(0x1337)
# Setting the UUID for the Audio RGB Receiving Service
_WRITE_RGB_ARRAY = (
    #bluetooth.UUID("0001A345-0003-6666-7777-888899990000"),
    bluetooth.UUID(0x1138),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
    )
# Creating a dummy characteristic to test functionality
_WRITE_RBG_DUMMY = (
    bluetooth.UUID("00000001-0004-6666-7777-888899990000"),
    _FLAG_WRITE,
    )
# Note: The purpose of the above function is to in-take RGB arrays of information related to audio

## Notification Testing
#   - Note: The notification will be sent regardless of the subscription status of the client to this characteristic.
# Setting the UUID for a Notification Testing Service
_NOTIFY_UUID = bluetooth.UUID("009071FE-0000-1111-2222-333344445555")
# Setting the UUID for the Read Notify Characteristic
_READ_NOTIFY_UUID = (
    bluetooth.UUID("009071FE-0001-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_NOTIFY,
    )
# Setting the UUID for the Write Notify + No Reponse Characteristic
#    - Note: "If send_update is True, then any subscribed clients will be notified (or indicated, depending on what they’re subscribed to and which operations the characteristic supports) about this write."
_WRITE_NOTIFY_NO_RESPONSE_UUID = (
    bluetooth.UUID("009071FE-0002-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_NOTIFY,
    )
# Setting the UUID for the Write Notify + Response Characteristic
_WRITE_NOTIFY_RESPONSE_UUID = (
    bluetooth.UUID("009071FE-0003-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_NOTIFY,
    )

## Indication Testing
#   - Note: The indication will be sent regardless of the subscription status of the client to this characteristic.
# Setting the UUID for an Indiciation Testing Service
_INDICATE_UUID = bluetooth.UUID("19D1CA7E-0000-1111-2222-333344445555")
# Setting the UUID for the Write Indiciation Characteristic
_READ_INDICATE_UUID = (
    bluetooth.UUID("19D1CA7E-0001-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_INDICATE,
    )
# Setting the UUID for the Write Indication + No Response Characteristic
_WRITE_INDICATE_NO_REPSONSE_UUID = (
    bluetooth.UUID("19D1CA7E-0002-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_INDICATE,
    )
# Setting the UUID for the Write Indication + Response Characteristic
_WRITE_INDICATE_RESPONSE_UUID = (
    bluetooth.UUID("19D1CA7E-0003-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_INDICATE,
    )

## Joint Notification and Indication Testing
# Setting the UUID for a Notification + Indication Testing Service
_NOTIFY_INDICATE_UUID = bluetooth.UUID("9071CA73-0000-1111-2222-333344445555")
# Setting the UUID for the Read Notify + Indiciate Characteristic
_READ_NOTIFY_INDICATE_UUID = (
    bluetooth.UUID("9071CA73-0001-1111-2222-333344445555"),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE,
    )
# Setting the UUID for the Write + No Reponse + Notify + Indicate Characteristic
_WRITE_NOTIFY_INDICATE_NO_RESPONSE_UUID = (
    bluetooth.UUID("9071CA73-0002-1111-2222-333344445555"),
    _FLAG_WRITE_NO_RESPONSE | _FLAG_NOTIFY | _FLAG_INDICATE,
    )
# Setting the UUID for the Write + Reponse + Notify + Indicate Characteristic
_WRITE_NOTIFY_INDICATE_RESPONSE_UUID = (
    bluetooth.UUID("9071CA73-0003-1111-2222-333344445555"),
    _FLAG_WRITE | _FLAG_NOTIFY | _FLAG_INDICATE,
    )

## Scratch Space for Adding the Defined Services and Characteristics to a deviced "Service Package"
# Configuring the BLE GATT Read Service
_READ_SERVICE = (
    _READ_UUID,
    (_READ_COUNTER, _READ_VARIABLE, _READ_ENCRYPTED, _READ_AUTHENTICATED, _READ_AUTHORIZED),
)
# Configuring the BLE GATT Write Service
_WRITE_SERVICE = (
    _WRITE_UUID,
    (_WRITE_GENERAL, _WRITE_VARIABLE, _WRITE_ENCRYPTED, _WRITE_AUTHENTICATED, _WRITE_AUTHORIZED, _WRITE_AUTHENTICATED_SIGNED, _WRITE_AUX, _WRITE_RESPONSE_GENERAL, _WRITE_RESPONSE_VARIABLE, _WRITE_NO_RESPONSE_ENCRYPTED, _WRITE_NO_RESPONSE_AUTHENTICATED, _WRITE_NO_RESPONSE_AUTHORIZED,  _WRITE_NO_RESPONSE_AUTHENTICATED_SIGNED, _WRITE_NO_RESPONSE_AUX),
)
# Configuring the BLE GATT RGB Service
_RBG_SERVICE = (
    _RGB_UUID,
    (_WRITE_RGB_ARRAY,),
)
# TODO: Create a notification characteristic that confirms operation || provides control
# Configuring the BLE GATT Notification Service
_NOTIFY_SERVICE = (
    _NOTIFY_UUID,
    (_READ_NOTIFY_UUID, _WRITE_NOTIFY_NO_RESPONSE_UUID, _WRITE_NOTIFY_RESPONSE_UUID),
)
# Configuring the BLE GATT Indication Services
_INDICATE_SERVICE = (
    _INDICATE_UUID,
    (_READ_NOTIFY_INDICATE_UUID, _WRITE_NOTIFY_INDICATE_NO_RESPONSE_UUID, _WRITE_NOTIFY_INDICATE_RESPONSE_UUID),
)
# Configuring the BLE GATT Notify + Indicate Service
_NOTIFY_INDICATE_SERVICE = (
    _NOTIFY_INDICATE_UUID,
    (_READ_NOTIFY_INDICATE_UUID, _WRITE_NOTIFY_INDICATE_NO_RESPONSE_UUID, _WRITE_NOTIFY_INDICATE_RESPONSE_UUID),
)

# Services List for Adding ALL services to the GATT Server
_SERVICES = (_UART_SERVICE, _READ_SERVICE, _WRITE_SERVICE, _RBG_SERVICE, _NOTIFY_SERVICE, _INDICATE_SERVICE, _NOTIFY_INDICATE_SERVICE)

#####
#
# Class Definitions - Ex: Simple BLE Peripheral Object
#
#####

# Class definition for the BLESimplePeripheral Object
class BLESimplePeripheral:
    def __init__(self, ble, name="mpy-uart"):
        # Sets the BLE object to the Class' internal property
        self._ble = ble
        # Sets the BLE radio to being on
        self._ble.active(True)
        # Registers a callback for events from the BLE stack; using the Class' _irq function at the BLE Object's callback
        self._ble.irq(self._irq)
        # Configures the server with the specified services; which replaces any existing services
        #((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        # Configures the Read Service into the Server
        #((self._handle__read_counter, self._handle__read_variable),) = self._ble.gatts_register_services((_READ_SERVICE,))
        # Configures the Write Service into the Server
        #((self._handle__write_general, self._handle__write_variable),) = self._ble.gatts_register_services((_WRITE_SERVICE,))
        # Nota Bene: According to the documentation this may need to be passed as a list of services
        #   - Ex:       SERVICES = (HR_SERVICE, UART_SERVICE,)
        #               ( (hr,), (tx, rx), ) = bt.gatts_register_services(SERVICES)
        # NOTE: The LAST instance of "ble.gatts_register_services()" dicates the ONLY services that will be available via the GATT Server
        # Configuration for EVERYTHING being visible
        #( (self._handle_tx, self._handle_rx), (self._handle__read_counter, self._handle__read_variable), (self._handle__write_general, self._handle__write_variable), (self._handle__rgb_array_write,), ) = self._ble.gatts_register_services(_SERVICES)
        #       [ _UART_SERVICE ]           ,                   [ _READ_SERVICE ]                       ,                   [ _WRITE_SERVICE]                               <------ General Breakdown of the Pointers Generated from the _SERVICES list
        ( 
            (self._handle_tx, self._handle_rx),     # UART
            (self._handle__read_counter, self._handle__read_variable, self._handle__read_encrypted, self._handle__read_authenticated, self._handle__read_authorized),   # READ
            (self._handle__write_general, self._handle__write_variable, self._handle__write_encrypted, self._handle__write_authenticated, self._handle__write_authorized, self._handle__write_authenticated_signed, self._handle__write_aux, self._handle__write_response_general, self._handle__write_response_variable, self._handle__write_no_response_encrypted, self._handle__write_no_response_authenticated, self._handle__write_no_response_authorized, self._handle__write_no_response_authenticated_signed, self._handle__write_no_response_aux),     # WRITE
            (self._handle__rgb_array_write,),   # RGB
            (self._handle__notify_read, self._handle__notify_write_no_response, self._handle__notify_write_response),   # NOTIFY
            (self._handle__indiciate_read, self._handle__indicate_write_no_response, self._handle__indicate_write_response),    # INDICATE
            (self._handle__notify_indicate_read, self._handle__notify_indicate_write_no_response, self._handle__notify_indicate_write_response),    # NOTIFY + INDICATE
         ) = self._ble.gatts_register_services(_SERVICES)
        # Other configuration
        self._connections = set()
        self._write_callback = None
        self._write_service__char_01__callback = None
        self._write_service__char_02__callback = None
        self._rgb_service__array_write__callback = None
        # Configure the payload for the advertising beacon(s); for identification during scan(s)
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        # Begin advertisement of the BLE Peripheral
        self._advertise()
        ## Initializations of internal values
        # Initialize the Read Service Characteristics
        self._ble.gatts_write(self._handle__read_counter, b'R-Serv Char 01')	#, send_update=False)
        self._ble.gatts_write(self._handle__read_variable, b'R-Serv Char Var')	#, send_update=True)
        # Note the configuration of the 'send_update' variable
        ## Set GATT buffer on the device
        #self._ble.gatts_set_buffer(<value_handle>, <len>, append=False,)   #   Note: Default is 20
        ## RGB Audio Initialization
        #self._ble.gatts_write(self._handle__rgb_array_write, b'RGB Array Intake')   #, send_update=True)       # Note: Only works for READ characteristics (or that have a READ attribute)
        self.LED_SWITCH = False 
        #self.oj_led = Pin(TEST__ORANGE_WIRE, Pin.OUT)

    # Function definition for BLE Event Handling
    #   - Note: There is a full example of all expected data breakdowns for each event within the micropython library listed above; THIS is WHERE knowledge of each OUTPUT COMES FROM
    def _irq(self, event, data):
        ## Connection Events
        # A central device has connected to this peripheral
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            #print("New connection", conn_handle)
            print("[+] New connection\t-\t[ {0} ]".format(conn_handle))
            self._connections.add(conn_handle)
        # A central device has disconnected to this peripheral
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            #print("Disconnected", conn_handle)
            print("[-] Disconnected\t-\t[ {0} ]".format(conn_handle))
            self._connections.remove(conn_handle)
            self._advertise()
        # Connection update event has occurred
        elif event == _IRQ_CONNECTION_UPDATE:
            print("[*] IRQ Connection Update has Occurred")
            print("\tEvent:\t\t{0}\n\tData:\t\t{1}".format(event, data))
            pass

        ## Write Events
        # A client has written to this Characteristic or Descriptor
        elif event == _IRQ_GATTS_WRITE:
            print("[*] Write Event Occuring")
            # Extract the Connection Hande ('conn_handle') and Value Handle ('value_handle') from the received data; Note: 'data' is an expected event variable(, or is it configured elsewhere?)
            conn_handle, value_handle = data
            # Extract the value of the data at the 'value_handle' via GATT
            value = self._ble.gatts_read(value_handle)
            print("\tValue:\t\t{0}\n\tValue Handle:\t{1}".format(value, value_handle))
            ## Breakdown of Write Event based on Intended Handle
            # Write action for regular function of UART RX line; NOTE: Pay attention to the self._write* properties being used as secondary checks for what function is called
            if value_handle == self._handle_rx and self._write_callback:
                print("[+] Making Callack since Value Handle [{0}] Matched Handle RX [{1}]".format(value_handle, self._handle_rx))
                # Call to the established function pointed to by 'self._write_callback()'
                self._write_callback(value)
            # Write action for the Write Service Characteristic 01
            elif value_handle == self._handle__write_general and self._write_service__char_01__callback:
                print("[+] Making W-Serv Char 01 Callback since Value Handle [{0}] Matched Handle RX [{1}]".format(value_handle, self._handle__write_general))
                self._write_service__char_01__callback(value)
            # Write action for the Write Service Characteristic 02
            elif value_handle == self._handle__write_variable and self._write_service__char_02__callback:
                print("[+] Making W-Serv Char 02 Callback since Value Handle [{0}] Matched Handle RX [{1}]".format(value_handle, self._handle__write_variable))
                self._write_service__char_02__callback(value)     ## TODO: Fix to make the correct callback function call
                #self._write_callback(value)
            # Write action for the RGB Array Write Characteristic
            elif value_handle == self._handle__rgb_array_write and self._rgb_service__array_write__callback:
                print("[+] Making RGB Array Write Callback since Value Handle [{0}] Matched Handle RX [{1}]".format(value_handle, self._handle__rgb_array_write))
                self._rgb_service__array_write__callback(value)

        # A client has completed a write event to a Characteristic or Descriptor
        elif event == _IRQ_GATTC_WRITE_DONE:
            print("[*] Write Event has Completed")

        ## Reading Events
        # A client has requests a read to this Characteristic or Descriptor
        elif event == _IRQ_GATTS_READ_REQUEST:
            print("[*] Read Request Event Occuring")
            #conn_handle, value_handle, unknown = data
            #conn_handle, value_handle = data
            conn_handle, attr_handle = data
            if dbg != 1:        # ~!~
                #print("[?] Debugging [ _IRQ_GATTS_READ_REQUEST ] Event\t\t-\t\tVariable Breakdown:\n\tConn Handle:\t\t{0}\n\tValue Handle:\t\t{1}\n\tUnknown Third Thing:\t{2}".format(conn_handle, value_handle, unknown))
                print("[?] Debugging [ _IRQ_GATTS_READ_REQUEST ] Event\t\t-\tVariable Breakdown:\n\tConn Handle:\t\t{0}\n\tAttr Handle:\t\t{1}".format(conn_handle, attr_handle))
            ## Note: Unsure how to capture the Response Code, may not need this here?
            '''
            _GATTS_NO_ERROR = const(0x00)
            _GATTS_ERROR_READ_NOT_PERMITTED = const(0x02)
            _GATTS_ERROR_WRITE_NOT_PERMITTED = const(0x03)
            _GATTS_ERROR_INSUFFICIENT_AUTHENTICATION = const(0x05)
            _GATTS_ERROR_INSUFFICIENT_AUTHORIZATION = const(0x08)
            _GATTS_ERROR_INSUFFICIENT_ENCRYPTION = const(0x0f)
            '''
        # A client has generated a result from a read event to a Characteristic or Descriptor
        elif event == _IRQ_GATTC_READ_RESULT :
            print("[*] Read Result Event Occuring")
            if dbg != 1:        # ~!~
                print("[?] Debugging [ _IRQ_GATTC_READ_RESULT ] Event\t\t-\t\tVariable Breakdown:\n\tData:\t\t{0}".format(data))
            # A gattc_read() has completed
            conn_handle, value_handle, char_data = data
        # A client has completed a read event to a Characteristic or Descriptor
        elif event == _IRQ_GATTC_READ_DONE:
            print("[*] Read Event has Completed")
            if dbg != 1:        # ~!~
                print("[?] Debugging [ _IRQ_GATTC_READ_DONE ] Event\t\t-\t\tVariable Breakdown:\n\tData:\t\t{0}".format(data))
            # A gattc_read() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data

        ## Scan Events
        # A single scan result; NOTE: This event is not defined
        elif event == _IRQ_SCAN_RESULT:
            print("[*] Single Scan Result:")
            addr_type, addr, adv_type, rssi, adv_data = data
            print("\tAddress Type:\t{0}\n\tAddress:\t\t{1}\n\tAdv Type:\t{2}\n\tRSSI:\t\t{3}\n\tAdv Data:\t\t{4}".format(addr_type, addr, adv_type, rssi, adv_data))
        # Scan duration finished or was manually stopped
        elif event == _IRQ_SCAN_DONE:
            print("[*] IRQ Scan Completed OR Stopped")
            pass

        ## Notification/Indicate Events
        # A GATT Notify Event has Occurred
        elif event == _IRQ_GATTC_NOTIFY:
            print("[*] GATT Notify Event Occuring")
            # A server has sent a notify request.
            conn_handle, value_handle, notify_data = data
            if dbg != 0:
                print("[+] IRQ Event::Notify Event:\t[ Connection Handle ]:{0}\t\t[ Value Handle ]:{1}\t\t[ Notify Data ]:{2}".format(conn_handle, value_handle, notify_data))
        # A GATT Indicate Event has Occurred
        elif event == _IRQ_GATTC_INDICATE: 
            print("[*] GATT Indicate Event Occuring")
            # A server has sent an indicate request.
            conn_handle, value_handle, notify_data = data
            if dbg != 0:
                print("[+] IRQ Event::Indicate Event:\t[ Connection Handle ]:{0}\t\t[ Value Handle ]:{1}\t\t[ Notify Data ]:{2}".format(conn_handle, value_handle, notify_data))
        # A GATT Indicate Event has Completed
        elif event == _IRQ_GATTS_INDICATE_DONE:
            print("[*] GATT Indicate Event has Completed")
            # A client has acknowledged the indication.
            # Note: Status will be zero on successful acknowledgment, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            if dbg != 0:
                print("[+] IRQ Event::Indicate Completed:\t[ Connection Handle ]:{0}\t\t[ Value Handle ]:{1}\t\t[ Status ]:{2}".format(conn_handle, value_handle, status))

        ## Services Events
        # Result from a service being discovered 
        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Called for each service found by gattc_discover_services().
            conn_handle, start_handle, end_handle, uuid = data
            print("[*] GATT Service Discovered by Scan")
            if dbg != 0:
                print("[+] IRQ Event::Service Result:\t[ Connection Handle ]:{0}\t\t[ Start Handle ]:{1}\t\t[ End Handle ]:{2}\t\t[ UUID ]:{3}".format(conn_handle, start_handle, end_handle, uuid))

        # Service discovery has completed
        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("[*] GATT Service Discovery has Completed")
            if dbg != 0:
                print("[+] IRQ Event::Service Done:\t[ Connection Handle ]:{0}\t\t[ Status ]:{1}".format(conn_handle, status))

        ## Characteristics Events
        # Result from a characteristic being discovered
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Called for each characteristic found by gattc_discover_services().
            conn_handle, end_handle, value_handle, properties, uuid = data
            print("[*] GATT Characteristic Discovered by Scan")
            if dbg != 0:
                print("[+] IRQ Event::Characteristic Result:\t[ Connection Handle ]:{0}\t\t[ End Handle ]:{1}\t\t[ Value Handle ]:{2}\t\t[ Properties ]:{3}\t\t[ UUID ]:{4}".format(conn_handle, end_handle, value_handle, properties, uuid))
        # Characteristic discovery has completed
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("[*] GATT Characteristic Discovery has Completed")
            if dbg != 0:
                print("[+] IRQ Event::Characteristic Done:\t[ Connection Handle ]:{0}\t\t[ Status ]:{1}".format(conn_handle, status))

        ## Descriptor Events
        # Result from a descriptor being discovered
        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            # Called for each descriptor found by gattc_discover_descriptors().
            conn_handle, dsc_handle, uuid = data
            print("[*] GATT Descriptor Discovered by Scan")
            if dbg != 0:
                print("[+] IRQ Event::Descriptor Result:\t[ Connection Handle ]:{0}\t\t[ Descriptor Handle ]:{1}\t\t[ UUID ]:{2}".format(conn_handle, dsc_handle, uuid))
        # Descriptor discovery has completed
        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("[*] GATT Descriptor Discovery has Completed")
            if dbg != 0:
                print("[+] IRQ Event::Descriptor Done:\t[ Connection Handle ]:{0}\t\t[ Status ]:{1}".format(conn_handle, status))

        ## L2CAP Events
        # An L2CAP Accept Event Occured
        elif event == _IRQ_L2CAP_ACCEPT:
            # A new channel has been accepted.
            # Return a non-zero integer to reject the connection, or zero (or None) to accept.
            conn_handle, cid, psm, our_mtu, peer_mtu = data
            print("[*] L2CAP Accept Event Occuring")
            if dbg != 0:
                print("[+] IRQ Event::L2CAP Accept:\t[ Connection Handle ]:{0}\t\t[ CID ]:{1}\t\t[ PSM ]:{2}\t\t[ Our MTU ]:{3}\t\t[ Peer MTU ]:{4}".format(conn_handle, cid, psm, our_mtu, peer_mtu))
        # An L2CAP Connect Event Occured
        elif event == _IRQ_L2CAP_CONNECT:
            # A new channel is now connected (either as a result of connecting or accepting).
            conn_handle, cid, psm, our_mtu, peer_mtu = data
            print("[*] L2CAP Connect Event Occuring")
            if dbg != 0:
                print("[+] IRQ Event::L2CAP Connect:\t[ Connection Handle ]:{0}\t\t[ CID ]:{1}\t\t[ PSM ]:{2}\t\t[ Our MTU ]:{3}\t\t[ Peer MTU ]:{4}".format(conn_handle, cid, psm, our_mtu, peer_mtu))
        # An L2CAP Disconnect Event Occured
        elif event == _IRQ_L2CAP_DISCONNECT:
            # Existing channel has disconnected (status is zero), or a connection attempt failed (non-zero status).
            conn_handle, cid, psm, status = data
            print("[*] L2CAP Disconnect Event Occuring")
            if dbg != 0:
                print("[+] IRQ Event::L2CAP Disconnect:\t[ Connection Handle ]:{0}\t\t[ CID ]:{1}\t\t[ PSM ]:{2}\t\t[ Status ]:{3}".format(conn_handle, cid, psm, status))
        # An L2CAP Received Event Occured
        elif event == _IRQ_L2CAP_RECV:
            # New data is available on the channel. Use l2cap_recvinto to read.
            conn_handle, cid = data
            print("[*] L2CAP Received Event Occuring")
            if dbg != 0:
                print("[+] IRQ Event::L2CAP Received:\t[ Connection Handle ]:{0}\t\t[ CID ]:{1}".format(conn_handle, cid))
        # An L2cap Send Ready Event Occured
        elif event == _IRQ_L2CAP_SEND_READY:
            # A previous l2cap_send that returned False has now completed and the channel is ready to send again.
            # If status is non-zero, then the transmit buffer overflowed and the application should re-send the data.
            conn_handle, cid, status = data
            print("[*] L2CAP Send Ready Event Occuring")
            if dbg != 0:
                print("[+] IRQ Event::L2CAP Send Ready:\t[ Connection Handle ]:{0}\t\t[ CID ]:{1}\t\t[ Status ]:{2}".format(conn_handle, cid, status))

        ## Secret Events
        # A Get Secret Event is Occuring
        elif event == _IRQ_GET_SECRET:
            print("[*] Get Secret Event Occuring")
            # Return a stored secret.
            # If key is None, return the index'th value of this sec_type.
            # Otherwise return the corresponding value for this sec_type and key.
            sec_type, index, key = data
            if dbg != 0:
                print("[+] IRQ Event::Get Secret:\t[ Sec Type ]:{0}\t\t[ Index ]:{1}\t\t[ Key ]:{2}".format(sec_type, index, key))
            return value
        # A Set Secret Event is Occuring
        elif event == _IRQ_SET_SECRET:
            print("[*] Set Secret Event Occuring")
            # Save a secret to the store for this sec_type and key.
            sec_type, key, value = data
            if dbg != 0:
                print("[+] IRQ Event::Set Secret:\t[ Sec Type ]:{0}\t\t[ Index ]:{1}\t\t[ Key ]:{2}".format(sec_type, key, value))
            return True

        ## Encryption Events
        elif event == _IRQ_ENCRYPTION_UPDATE:
            print("[*] Encryption Update Event Occuring")
            # The encryption state has changed (likely as a result of pairing or bonding).
            conn_handle, encrypted, authenticated, bonded, key_size = data
            if dbg != 0:
                print("[+] IRQ Event::Encryption Update:\t[ Conneciton Handle ]:{0}\t\t[ Encrypted ]:{1}\t\t[ Authenticated ]:{2}\t\t[ Bonded ]:{3}\t\t[ Key Size ]:{4}".format(conn_handle, encrypted, authenticated, bonded, key_size))

        ## Passkey Action Events
        elif event == _IRQ_PASSKEY_ACTION:
            print("[*] Passkey Action Event Occuring")
            # Respond to a passkey request during pairing.
            # See gap_passkey() for details.
            # action will be an action that is compatible with the configured "io" config.
            # passkey will be non-zero if action is "numeric comparison".
            conn_handle, action, passkey = data
            if dbg != 0:
                print("[+] IRQ Event::Passkey Action:\t[ Connection Handle ]:{0}\t\t[ Action ]:{1}\t\t[ Passkey ]:{2}".format(conn_handle, action, passkey))
        
        ## Unknown/Unexpected Events
        # Unknown Debugging Check for IRQ
        else:
            if dbg != 0:    # ~!~
                print("[!] Unkonwn [ _IRQ ] Event Occured!\n\tEvent\t\t{0}\n\tData:\t\t{1}".format(event, data))

    # Function for sending the notification to ALL connected devices
    def send(self, data):
        # Iterate through each device (i.e. conn_handle) connected to the BLE Server (i.e. self._connections)
        for conn_handle in self._connections:
            if dbg != 0:
                print("[*] Sending Notification to Conection Handle [ {0} ]\t\t-\t\tData:\t[ {1} ]".format(conn_handle, data))
            # Sends a notification request to the connected client
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)
            # Getting odd error around here, might be part of additions above

    # Function for writing data to a given attribute handle
    def write_to_attribute(self, attribute_handle, data):
        # Write to the specified attribute_handle
        self._ble.gatts_write(attribute_handle, data)

    # Function for reading data from a given attribute handle
    def read_from_attribute(self, attribute_handle):
        # Read from the specified attribute_handle
        data = self._ble.gatts_read(attribute_handle)
        # Return the read data
        return data

    # Function for testing if there are any existing connections via conn_handles in self._connections
    def is_connected(self):
        return len(self._connections) > 0

    # Internal function for advertising the BLE GAP Service
    def _advertise(self, interval_us=500000):
        print("[*] Starting advertising")
        # Call to advertise using the provided payload-data
        self._ble.gap_advertise(interval_us, adv_data=self._payload)
        # Note: adv_data is included in all broadcasts; where resp_data is sent in reply to an active scan

    # Internal function for having a callback after a write occurs
    def on_write(self, callback):
        self._write_callback = callback
        # Nota Bene: Through testing was found that at most 21 characters can be received by a write

    # Internal function for having a callback after a write occurs to Write Service Characteristic 02
    def w_serv__char_01(self, callback):
        self._write_service__char_01__callback = callback
        # Nota Bene: Without aleration of the buffer, the limit of the buffer is 20 characters

    # Internal function for having a callback after a write occurs to Write Service Characteristic 02
    def w_serv__char_02(self, callback):
        self._write_service__char_02__callback = callback
        # Nota Bene: Without aleration of the buffer, the limit of the buffer is 20 characters

    # Internal function for having a callback after a write occurs to RGB Array Write Characteristic
    def rgb_serv__array_write(self, callback):
        self._rgb_service__array_write__callback = callback


def demo():
    # Configure local Pin LED to OUT
    led_onboard = Pin("LED", Pin.OUT)
    # Creating a BLE bluetooth device
    ble = bluetooth.BLE()
    # Passing the BLE device to the BLESimplePeripheral Class
    #p = BLESimplePeripheral(ble, "mpy-audio")   # Note: This causes the 0x1800 to return "MPY BTSTACK"
    p = BLESimplePeripheral(ble)
    # Variable for internal tracking (used to be read by Read Service's first Characteristic)
    read_count = 0
    # Variable for internal ouptut (used to be read by Read Service's second Characteristic)
    read_output = "< No Output >"

    # Sub-function for use as callback function that reads the internal read_count variable
    def read_action__count(v):
        ## TODO: Figure out how to have this action be performed by the read characteristic
        print("[*] Setting internal variable to 'read_count' value")
        # Note: The code below writes to the read_counter handle the value that is passed to it, and NOT the internal counter variable
        #p._ble.gatts_write(p._handle__read_counter, v)  #, send_update=False,)       # Note: Might need to remove the 'send_update' part of this
        # Write the 'read_count' variable to the R-Serv Characteristic 01
        p._ble.gatts_write(p._handle__read_counter, str(read_count))
        print("[+] GATT write to the R-Serv Characteristic 01")
        print("[*] Read Service Characteristic 01:\t\t{0}".format(p._ble.gatts_read(p._handle__read_counter,)))
        print("[+] Read Count Variable Passed:\t\t{0}".format(v))

    # Sub-function for use as callback function that reads the internal read_update variable
    def read_action__output(v):
        # Set the internal variable to contain the value desired
        print("[*] Setting internal variable to 'read_output' value")
        p._ble.gatts_write(p._handle__read_variable, v) #, send_update=False,)      # Note: Might need to remove the 'send_update' part of this
        print("[+] GATT write to the R-Serv Characteristic 02")
        # Read the value written to the GATT Characteristic
        print("[*] Read Service Characteristic 02:\t\t{0}".format(p._ble.gatts_read(p._handle__read_variable,)))
        print("[*] Read Output Variable Passed:\t\t{0}".format(v))

    # Sub-function for use as callback function
    def on_rx(v):
        #print("RX", v)
        print("[+] RX:\t\t{0}".format(v))

    # Sub-function for use as callback function that processes and confirms receiving RGB array information
    def rgb_array__receive(v):
        # Sub-sub-function for performing LED changes
        def change_led(led_object):
            # Change the value of the LED Pin
            if led_object.value():
                led_object.off()
            else:
                led_object.on()

        # Sub-sub-function for tokenizing RGB array data
        def parse_rgb(rgb_input_byte_string):
            # Extract the pieces of RGB information
            if len(rgb_input_byte_string) < 1:
                red_led_pwm = 0
                green_led_pwm = 0
                blue_led_pwm = 0
            elif len(rgb_input_byte_string) < 2:
                red_led_pwm = rgb_input_byte_string[0]
                green_led_pwm = 0
                blue_led_pwm = 0
            elif len(rgb_input_byte_string) < 3:
                red_led_pwm = rgb_input_byte_string[0]
                green_led_pwm = rgb_input_byte_string[1]
                blue_led_pwm = 0
            elif len(rgb_input_byte_string) < 4:
                red_led_pwm = rgb_input_byte_string[0]
                green_led_pwm = rgb_input_byte_string[1]
                blue_led_pwm = rgb_input_byte_string[2]
            else:
                red_led_pwm = rgb_input_byte_string[0]
                green_led_pwm = rgb_input_byte_string[1]
                blue_led_pwm = rgb_input_byte_string[2]
                trash_data = rgb_input_byte_string[2:]
            # Debug print-out
            print("[+] Parsed RGB of {0} into R [ {1} ], G [ {2} ], B [ {3} ]".format(rgb_input_byte_string, red_led_pwm, green_led_pwm, blue_led_pwm))
            # Return LED PWM values
            return red_led_pwm, green_led_pwm, blue_led_pwm

        print("[+] RGB Array:\t\t{0}".format(v))
        ## Basic LED Testing
        if not LED_PWM:
            # Flip the Value for the Orange LED
            #oj_led = Pin(TEST__ORANGE_WIRE, LED_SWITCH)
            p.LED_SWITCH = not p.LED_SWITCH
            #oj_led.value(LED_SWITCH)
            #oj_led.on()
            print("\tLED SWITCH Value:\t\t{0}".format(p.LED_SWITCH))
            # Test Change LED
            change_led(oj_led)
            ## Setting LEDs Using RGB Parsed Data; Basic On/Off variation
            red, green, blue = parse_rgb(v)
            # Set Red
            if red != 0:
                yl_led.on()
            else:
                yl_led.off()
            # Set Green
            if green != 0:
                oj_led.on()
            else:
                oj_led.off()
            # Set Blue
            if blue != 0:
                wt_led.on()
            else:
                wt_led.off()
        ## PWM LED Testing
        else:
            # Parse PWMs for RGB
            red, green, blue = parse_rgb(v)
            # Set Red
            oj_pwm.duty_u16(pwm_duty_step * red)
            # Set Green
            yl_pwm.duty_u16(pwm_duty_step * green)
            # Set Blue
            wt_pwm.duty_u16(pwm_duty_step * blue)

    # Sub-sub-function for reading a local input file
    def read_local_rgb_test(input_test_filename="audio-to-rgb.conversion"):
        ## Configuration opening the provided (or default) file
        #input_test_filename="audio-to-rgb.conversion"
        conversion_debugging_input = open(input_test_filename, 'r')
        #first_time_completed = 0
        ## Read the file from the location
        

    # Setting the callback function for the on_write() function
    p.on_write(on_rx)
    ## TODO: Understand how to use the above function format to perform the 'w_serv__char_02' internal function call
    # Setting the callback function for the [W-Serv Char 01] w_serv__char_01() function
    p.w_serv__char_01(read_action__count)
    # Setting the callback function for the [W-Serv Char 02] w_serv__char_02() function
    p.w_serv__char_02(read_action__output)
    # Setting the callback function for the [RGB Array Write] rgb_array__write() function
    p.rgb_serv__array_write(rgb_array__receive)
    # Setting the callback function for the [Notification Read] _________ function
    
    # Setting the callback function for the [Notification Write] __________ function
    
    # Setting the callback function for the [Indication Read] __________ function
    
    # Setting the callback function for the [Indication Write] ___________ function
    

    # While loop for tracking timing on TX checking
    i = 0
    while True:
        # Only perform the TX tracking if a device is connected to the Class Object
        if p.is_connected():
            # Turn on the LED on the Pico W
            led_onboard.on()
            for _ in range(3):
                data = str(i) + "_"
                #print("TX", data)
                if dbg != 0:
                    print("[*] TX:\t\t{0}".format(data))
                # Nota Bene: Due to the documentation, the nested gattc_notify/gattc_indicate call sends to ALL connected devices REGARDLESS of the subscription status; might be gatts_notify ??
                if demo_notify_flag != 0:
                    if dbg != 0:
                        print("[+] Sending notification from server")
                    p.send(data)
                else:
                    if dbg != 0:
                        print("[-] Not sending notification from server")
                # Update read_count
                read_count = i
                # Increase the value of i
                i += 1
        # Timing sleep (1/10th of a second)
        time.sleep_ms(100)
        # Change an LED?


if __name__ == "__main__":
    print("[*] Beginning Demo")
    demo()
    print("[+] Completed Demo")

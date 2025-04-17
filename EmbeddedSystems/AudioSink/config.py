"""
Config file for Raspberry Pi Pico W BLE Audio Sink

Contains pin definitions, audio configuration, and BLE settings.
"""
from micropython import const

# ========== Device Information ==========
BLE_DEVICE_NAME = "Pico-W-Audio"
MANUFACTURER_NAME = "Raspberry Pi Foundation"
MODEL_NUMBER = "Pico W Audio Sink"
FIRMWARE_VERSION = "1.0.0"

# ========== Hardware Pins (Based on README.wiring) ==========
# I2S pins for UDA1334A
I2S_BCK_PIN = const(16)  # I2S Bit Clock (SCK)
I2S_WS_PIN = const(17)   # I2S Word Select (LRCK)
I2S_SD_PIN = const(18)   # I2S Serial Data (DIN)

# Additional hardware pins
STATUS_LED_PIN = const(25)  # Onboard LED pin for Pico W
UDA_MUTE_PIN = const(22)    # Mute pin on UDA1334A (active low)

# ========== Audio Configuration ==========
AUDIO_SAMPLE_RATE = const(22050)    # Reduced from 44.1 kHz to 22.05 kHz
AUDIO_BIT_DEPTH = const(16)         # 16-bit audio
AUDIO_CHANNELS = const(2)           # Stereo
AUDIO_BUFFER_SIZE = const(2048)     # Reduced from 8192 to 2048 bytes
AUDIO_CHUNK_SIZE = const(256)       # Reduced from 512 to 256 bytes

# ========== BLE Configuration ==========
BLE_AUDIO_PACKET_SIZE = const(240)  # Reduced from 512 to 240 bytes
BLE_MTU_SIZE = const(240)           # Reduced from 512 to 240 bytes

# Advertising parameters
ADV_INTERVAL_MS = const(250)        # Advertising interval in milliseconds
SCAN_WINDOW_MS = const(1000)        # Scan window in milliseconds

# ========== BLE IRQ Event Codes ==========
BLE_IRQ_CENTRAL_CONNECT = const(1)
BLE_IRQ_CENTRAL_DISCONNECT = const(2)
BLE_IRQ_GATTS_WRITE = const(3)
BLE_IRQ_GATTS_READ_REQUEST = const(4)
BLE_IRQ_SCAN_RESULT = const(5)
BLE_IRQ_SCAN_DONE = const(6)
BLE_IRQ_PERIPHERAL_CONNECT = const(7)
BLE_IRQ_PERIPHERAL_DISCONNECT = const(8)
BLE_IRQ_GATTC_SERVICE_RESULT = const(9)
BLE_IRQ_GATTC_SERVICE_DONE = const(10)
BLE_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
BLE_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
BLE_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
BLE_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
BLE_IRQ_GATTC_READ_RESULT = const(15)
BLE_IRQ_GATTC_READ_DONE = const(16)
BLE_IRQ_GATTC_WRITE_DONE = const(17)
BLE_IRQ_GATTC_NOTIFY = const(18)
BLE_IRQ_GATTC_INDICATE = const(19)
BLE_IRQ_GATTS_INDICATE_DONE = const(20)
BLE_IRQ_MTU_EXCHANGED = const(21)
BLE_IRQ_L2CAP_ACCEPT = const(22)
BLE_IRQ_L2CAP_CONNECT = const(23)
BLE_IRQ_L2CAP_DISCONNECT = const(24)
BLE_IRQ_L2CAP_RECV = const(25)
BLE_IRQ_L2CAP_SEND_READY = const(26)
BLE_IRQ_CONNECTION_UPDATE = const(27)
BLE_IRQ_ENCRYPTION_UPDATE = const(28)
BLE_IRQ_GET_SECRET = const(29)
BLE_IRQ_SET_SECRET = const(30)

# ========== BLE Service UUIDs ==========
BLE_DEVICE_INFO_SERVICE_UUID = const(0x180A)
BLE_AUDIO_SERVICE_UUID = const(0x1843)  # Custom Audio Service
BLE_AUDIO_CONTROL_SERVICE_UUID = const(0x1844)  # Custom Audio Control Service

# ========== BLE Characteristic UUIDs ==========
BLE_MANUFACTURER_NAME_CHAR_UUID = const(0x2A29)
BLE_MODEL_NUMBER_CHAR_UUID = const(0x2A24)
BLE_FIRMWARE_REVISION_CHAR_UUID = const(0x2A26)

BLE_AUDIO_DATA_CHAR_UUID = const(0x2A3D)  # Audio data characteristic
BLE_AUDIO_CONTROL_CHAR_UUID = const(0x2A3E)  # Control commands characteristic
BLE_AUDIO_STATUS_CHAR_UUID = const(0x2A3F)  # Status notifications characteristic

# ========== Control Commands ==========
# Commands that can be sent via BLE
CMD_PLAY = const(0x01)
CMD_PAUSE = const(0x02)
CMD_STOP = const(0x03)
CMD_VOLUME_UP = const(0x04)
CMD_VOLUME_DOWN = const(0x05)
CMD_MUTE = const(0x06)
CMD_UNMUTE = const(0x07)
CMD_SET_SAMPLE_RATE = const(0x08)

# ========== Status Codes ==========
STATUS_READY = const(0x00)
STATUS_PLAYING = const(0x01)
STATUS_PAUSED = const(0x02)
STATUS_STOPPED = const(0x03)
STATUS_ERROR = const(0xFF)

# ========== Debug Configuration ==========
DEBUG_MODE = True
DEBUG_PRINT_INTERVAL = const(5)  # Seconds between debug prints 
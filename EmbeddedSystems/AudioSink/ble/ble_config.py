"""
BLE Audio Sink - Configuration

This module contains the configuration constants and settings
for the BLE audio sink implementation.
"""

from micropython import const

# BLE Device Information
DEVICE_NAME = "Pico-W BLE Audio Sink"
MANUFACTURER_NAME = "MicroPython"
MODEL_NUMBER = "Pico-W Audio Sink v1.0"
SOFTWARE_VERSION = "1.0.0"

# UUID Constants
# Standard service UUIDs
SVC_DEVICE_INFO = const(0x180A)       # Device Information service
SVC_AUDIO = const(0x1843)             # Audio service (using a pre-defined UUID)

# Custom service UUIDs
SVC_AUDIO_CONTROL = const(0x1844)     # Custom audio control service

# Characteristic UUIDs
# Device Information characteristics
CHAR_MANUFACTURER_NAME = const(0x2A29)
CHAR_MODEL_NUMBER = const(0x2A24)
CHAR_SOFTWARE_REV = const(0x2A28)

# Audio characteristics
CHAR_AUDIO_DATA = const(0x2A3D)       # Audio Data
CHAR_AUDIO_CONTROL = const(0x2A3C)    # Audio Control
CHAR_AUDIO_STATUS = const(0x2A3E)     # Audio Status

# BLE Configuration
BLE_IRQ_CENTRAL_CONNECT = const(1)
BLE_IRQ_CENTRAL_DISCONNECT = const(2)
BLE_IRQ_GATTS_WRITE = const(3)
BLE_IRQ_GATTS_READ = const(4)
BLE_IRQ_SCAN_RESULT = const(5)
BLE_IRQ_SCAN_COMPLETE = const(6)
BLE_IRQ_PERIPHERAL_CONNECT = const(7)
BLE_IRQ_PERIPHERAL_DISCONNECT = const(8)
BLE_IRQ_GATTS_INDICATE_DONE = const(9)
BLE_IRQ_MTU_EXCHANGED = const(10)
BLE_IRQ_L2CAP_ACCEPT = const(11)
BLE_IRQ_L2CAP_CONNECT = const(12)
BLE_IRQ_L2CAP_DISCONNECT = const(13)
BLE_IRQ_L2CAP_RECV = const(14)
BLE_IRQ_L2CAP_SEND_READY = const(15)
BLE_IRQ_CONNECTION_UPDATE = const(16)
BLE_IRQ_ENCRYPTION_UPDATE = const(17)
BLE_IRQ_GET_SECRET = const(18)
BLE_IRQ_SET_SECRET = const(19)

# Advertising parameters
ADV_INTERVAL_MS = const(250)
ADV_TYPE = const(0x02)      # ADV_NONCONN_IND - Non-connectable undirected advertising
CONN_ADV_TYPE = const(0x00) # ADV_IND - Connectable undirected advertising

# Audio configuration
AUDIO_SAMPLE_RATE = const(44100)  # Sample rate in Hz
AUDIO_BIT_DEPTH = const(16)       # Bit depth (16 or 32)
AUDIO_CHANNELS = const(2)         # Number of channels (1=mono, 2=stereo)
AUDIO_I2S_BUFFER = const(4096)    # I2S buffer size in bytes

# Buffer configuration
AUDIO_BUFFER_TARGET_MS = const(200)  # Target buffer size in milliseconds
AUDIO_CHUNK_SIZE = const(512)        # Size of each audio chunk to output in bytes

# Control commands (sent via CHAR_AUDIO_CONTROL)
CMD_PLAY = const(0x01)    # Start playback
CMD_PAUSE = const(0x02)   # Pause playback
CMD_STOP = const(0x03)    # Stop playback
CMD_NEXT = const(0x04)    # Next track
CMD_PREV = const(0x05)    # Previous track
CMD_VOL_UP = const(0x06)  # Volume up
CMD_VOL_DOWN = const(0x07)# Volume down
CMD_MUTE = const(0x08)    # Mute
CMD_UNMUTE = const(0x09)  # Unmute

# Status codes (sent via CHAR_AUDIO_STATUS)
STATUS_READY = const(0x00)     # Ready for connection/playback
STATUS_PLAYING = const(0x01)   # Playing audio
STATUS_PAUSED = const(0x02)    # Paused
STATUS_STOPPED = const(0x03)   # Stopped
STATUS_ERROR = const(0xFF)     # Error state

# GPIO Pin Configuration
I2S_SCK_PIN = const(10)  # I2S SCK (Serial Clock) - connected to BCK on UDA1334A
I2S_WS_PIN = const(11)   # I2S WS (Word Select) - connected to LRCK on UDA1334A
I2S_SD_PIN = const(12)   # I2S SD (Serial Data) - connected to DIN on UDA1334A

# UDA1334A Control Pins
UDA_MUTE_PIN = const(13)  # Mute pin on UDA1334A (active low)
UDA_SF0_PIN = const(14)   # SF0 pin on UDA1334A (system format)
UDA_SF1_PIN = const(15)   # SF1 pin on UDA1334A (system format) 
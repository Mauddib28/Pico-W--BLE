# Pico-W--BLE
BLE Practice with the Pico W

## More Resources
Found the originating BTstack that acts as the basis of the pico-w bt stack
	- URL:		https://bluekitchen-gmbh.com/btstack/#examples/examples/index.html


## BLE LED Driver
+-------------------------+           +---------------------------+
|     BLE GATT Server     |           |       LED Controller      |
|                         |           |                           |
|  +-------------------+  |           |  +--------------------+   |
|  |   LED Service     |  |           |  |    PWM Controller  |   |
|  |   (UUID: 0xA100)  |  |           |  |                    |   |
|  +-------------------+  |           |  |  +--------------+  |   |
|         |               |           |  |  | Red (GPIO17) |  |   |
|         |               |           |  |  +--------------+  |   |
|  +-------------------+  |    Write  |  |  +--------------+  |   |
|  | RGB Characteristic|<-|-----------|->|  |Green (GPIO22)|  |   |
|  | (UUID: 0xA101)    |  |           |  |  +--------------+  |   |
|  +-------------------+  |           |  |  +--------------+  |   |
|         |               |           |  |  |Blue (GPIO16) |  |   |
|         |               |           |  |  +--------------+  |   |
|  +-------------------+  |           |  +--------------------+   |
|  |Status Characteristic| |           |                           |
|  | (UUID: 0xA102)     | |           |  +--------------------+   |
|  +-------------------+  |           |  |  Onboard LED       |   |
|                         |           |  |  (Connection       |   |
|                         |           |  |   indicator)       |   |
+-------------------------+           +---------------------------+

## BLE E-Ink Demo

Boot Screen:
+----------------------------+
|                            |
| WaveShare                  |
| ePaper-2.13_V4            |
| Raspberry Pico WH         |
| Bluetooth Low Energy      |
|    GATT Server            |
|                            |
+----------------------------+

Ready Screen:
+----------------------------+
|                            |
| Ready for BLE              |
|                            |
+----------------------------+

Client Text Display:
+----------------------------+
|                            |
| [Client Text Here]         |
|                            |
+----------------------------+

Boot → Initialize Display → Display Test Pattern → Clear Display → 
Enter BLE Ready State → Display "Ready for BLE" →
↓
[Client Connects] → Toggle LED → Update Status to "Connected" →
↓                                                               ↑
[Receive Text] → Update Display → Update Status → [Remain Connected]
↓
[Client Disconnects] → Update Status to "Disconnected" → Return to BLE Ready State
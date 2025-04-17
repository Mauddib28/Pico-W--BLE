# Raspberry Pi Pico W - BLE Audio Sink

A Bluetooth Low Energy (BLE) Audio Sink implementation for the Raspberry Pi Pico W. This project enables the Pico W to receive audio data over BLE and output it through an I2S interface to a UDA1334A audio DAC.

## Features

- BLE Audio streaming using custom services and characteristics
- I2S audio output compatible with UDA1334A audio DAC
- Asynchronous architecture for efficient resource usage
- Audio controls (play/pause, volume)
- Status indication through onboard LED
- Memory monitoring and garbage collection
- Configurable audio parameters (sample rate, bit depth, channels)

## Hardware Requirements

- Raspberry Pi Pico W
- Adafruit I2S Stereo Decoder Breakout - UDA1334A
- Jumper wires
- Speaker or headphones with 3.5mm jack
- Power supply (USB or battery)

## Wiring Guide

Connect the Pico W to the UDA1334A as follows:

| Pico W Pin | UDA1334A Pin | Function       |
|------------|--------------|----------------|
| GPIO 16    | BCLK         | I2S Bit Clock  |
| GPIO 17    | LRCLK        | I2S Word Select|
| GPIO 18    | DIN          | I2S Serial Data|
| 3.3V       | VIN          | Power          |
| GND        | GND          | Ground         |

*For more detailed wiring information, refer to the [README.wiring](./README.wiring) file.*

## Software Architecture

The project follows a clean, modular architecture with clear separation of concerns:

### Component Separation

- **BLE Core (`ble/ble_core.py`)**: Handles all BLE functionality 
  - Service and characteristic setup
  - Connection management
  - Advertisement control
  - Data handling via callbacks

- **I2S Driver (`audio/i2s_driver.py`)**: Manages I2S audio output
  - Low-level I2S protocol implementation
  - Audio buffer management
  - Volume control
  - Asynchronous playback

- **BLE-Audio Adapter (`audio/ble_audio_adapter.py`)**: Connects BLE input to I2S output
  - Audio data routing
  - Command translation
  - Status tracking
  - Buffer management

- **Configuration (`config.py`)**: Centralized configuration
  - Hardware pin definitions
  - BLE service and characteristic UUIDs
  - Audio parameters
  - Status and command codes

- **Main Application (`main.py`)**: System entry point
  - Initialize components
  - Start background tasks
  - Handle user interaction

### Data Flow

1. BLE device connects to the Pico W
2. Audio data received via BLE is passed to the adapter
3. Adapter processes and queues audio data
4. I2S driver outputs audio data to the UDA1334A
5. Control commands flow from BLE to the adapter to control playback

### Key Design Principles

- **Centralized Configuration**: All constants and settings are in one place (`config.py`)
- **Asynchronous Processing**: Using `uasyncio` for non-blocking operations
- **Callback-Based Communication**: Components interact through well-defined callbacks
- **Resource Efficiency**: Memory monitoring and garbage collection for stable operation
- **Testability**: Each component has dedicated test functions

## Installation

1. Install the latest MicroPython firmware with BLE support on your Pico W
2. Clone this repository or download the files
3. Copy all files to the Pico W using a tool like Thonny IDE or `mpremote`
4. Reset the Pico W to start the application

```bash
# Example using mpremote
mpremote cp -r EmbeddedSystems/AudioSink/ :
```

## Usage

1. Power up the Pico W
2. The onboard LED will blink rapidly to indicate it's advertising
3. Connect to the device named "Pico-W-Audio" using a BLE audio source
4. Once connected, the LED will blink slowly
5. When audio data starts flowing, the LED will stay on continuously

## Testing

The project includes a comprehensive test framework:

- **Component Tests**: Each component has individual tests
  - `ble/ble_core.py`: Tests BLE functionality in isolation
  - `audio/i2s_driver.py`: Tests I2S output with tone generation
  - `audio/ble_audio_adapter.py`: Tests adapter functionality

- **Integration Tests**: The `run_tests.py` script tests all components together
  - Memory management tests
  - I2S audio output tests
  - BLE connectivity tests
  - Full system integration test

To run tests:
```
import run_tests
run_tests.main()
```

## BLE Protocol Specification

### Services

- **Device Information Service (0x180A)**
  - Manufacturer Name (0x2A29)
  - Model Number (0x2A24)
  - Firmware Revision (0x2A26)

- **Audio Service (0x1843)**
  - Audio Data Characteristic (0x2A3D) - Write

- **Audio Control Service (0x1844)**
  - Control Commands Characteristic (0x2A3E) - Write
  - Status Notifications Characteristic (0x2A3F) - Notify

### Control Commands

Control commands are sent as bytes with the following format:

1. **Play/Pause (0x01)**
   - Data: `[0x01, state]`
   - `state`: 0 = pause, 1 = play

2. **Volume (0x02)**
   - Data: `[0x02, volume]`
   - `volume`: 0-255 (mapped to 0.0-1.0)

3. **Latency Adjustment (0x03)**
   - Data: `[0x03, latency_low, latency_high]`
   - 16-bit value representing latency in milliseconds

## Troubleshooting

### No Sound
- Check the wiring connections between Pico W and UDA1334A
- Ensure the UDA1334A is receiving power (3.3V)
- Verify the I2S pins are correctly defined in `config.py`
- Check that speakers or headphones are properly connected

### BLE Connection Issues
- Ensure your BLE source device is compatible
- Check that the Pico W is advertising (fast blinking LED)
- Reset the Pico W and try reconnecting

### Audio Quality Issues
- Adjust the buffer sizes in `config.py`
- Check for interference in the I2S wiring
- Try reducing the CPU clock frequency if overclocking causes issues

## Contributing

Contributions to this project are welcome. Please feel free to submit a Pull Request.

## License

This project is released under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Adafruit for the UDA1334A breakout board
- Raspberry Pi Foundation for the Pico W
- MicroPython community for the BLE and I2S implementations 
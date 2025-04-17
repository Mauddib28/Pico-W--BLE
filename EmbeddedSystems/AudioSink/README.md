# Bluetooth Audio Speaker/Headset Project

This project implements a Bluetooth Low Energy (BLE) Audio Sink Device using a Raspberry Pi Pico WH and an Adafruit I2S Stereo Decoder. It enables audio data transmission over BLE protocol to the Pico WH, which then sends the audio to speakers/headphones via the I2S Stereo Decoder.

## Project Overview

The Bluetooth Audio Speaker/Headset device allows audio data to be transmitted from a BLE source device (like a smartphone) to the Pico WH, which then outputs the audio through connected speakers or headphones. Due to BLE limitations, the audio is transmitted through a custom L2CAP channel implementation rather than standard Bluetooth audio profiles.

## Features

- BLE connectivity with "BLE Audio Sink" and "BLE I2S" advertising names
- Media controls (play, pause, resume, stop) via BLE GATT service
- Volume control via BLE
- Status reporting for connected devices
- Command-line interface via serial connection
- I2S audio output through Adafruit UDA1334A Stereo Decoder

## Hardware Requirements

- Raspberry Pi Pico WH
- Adafruit I2S Stereo Decoder - UDA1334A Breakout board
- Jumper wires
- Headphones or speakers with 3.5mm jack

## Software Requirements

- Thonny IDE (or other MicroPython IDE)
- MicroPython firmware for Raspberry Pi Pico W
- MicroPython BLE modules
- MicroPython I2S modules

## Directory Structure

- `main.py`: Main MicroPython script
- `ble/`: BLE implementation files
  - `ble_config.py`: BLE configuration and functions
- `audio/`: Audio processing files
  - `audio_config.py`: Audio processing configuration and functions
- `i2s/`: I2S communication files
  - `i2s_config.py`: I2S interface configuration and functions
- `serial/`: Serial interface files
  - `serial_interface.py`: Serial command interface implementation
- `docs/`: Additional documentation
- `tests/`: Test scripts and utilities

## Getting Started

1. See `README.wiring` for hardware connection details
2. Install Thonny IDE from https://thonny.org/
3. Install MicroPython firmware on your Pico WH:
   - Connect Pico WH to your computer while holding the BOOTSEL button
   - In Thonny, go to Tools → Options → Interpreter
   - Select "MicroPython (Raspberry Pi Pico)"
   - Click "Install or update firmware"
   - Select the Pico W firmware and follow the instructions
4. Copy the project files to your Pico WH
5. Run `main.py` to start the application

## Usage

### BLE Connection
1. Power on the device
2. Search for "BLE Audio Sink" on your BLE source device
3. Connect to the device
4. Start playing audio from your source device

### Serial Interface
1. Connect to the device via USB
2. Open Thonny's Shell or use another serial terminal (115200 baud)
3. Type `help` to see available commands
4. Use commands like `play`, `pause`, `stop`, and `volume 80` to control the device

## Known Limitations

- BLE audio has limited bandwidth compared to Bluetooth Classic
- Audio quality may be affected by BLE throughput limitations
- No support for standard Bluetooth audio profiles (A2DP, AVRCP)
- MicroPython performance may limit audio processing capabilities

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
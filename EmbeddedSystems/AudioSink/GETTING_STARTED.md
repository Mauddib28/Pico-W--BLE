# Getting Started with BLE Audio Sink

This guide will help you quickly set up and start using the BLE Audio Sink on your Raspberry Pi Pico W.

## 1. Hardware Setup

### Components Needed

- Raspberry Pi Pico W
- Adafruit I2S Stereo Decoder Breakout - UDA1334A
- 5 jumper wires
- Speaker or headphones with 3.5mm jack
- Micro USB cable for power and programming

### Wiring

Connect the Pico W to the UDA1334A as follows:

| Pico W Pin | UDA1334A Pin | Wire Color (suggested) |
|------------|--------------|------------------------|
| GPIO 16    | BCLK         | Blue                   |
| GPIO 17    | LRCLK        | Yellow                 |
| GPIO 18    | DIN          | Green                  |
| 3.3V       | VIN          | Red                    |
| GND        | GND          | Black                  |

Connect headphones or speakers to the 3.5mm jack on the UDA1334A breakout board.

## 2. Software Setup

### Install MicroPython

1. Download the latest MicroPython firmware for Raspberry Pi Pico W from the [official website](https://micropython.org/download/rp2-pico-w/)
2. Hold the BOOTSEL button on the Pico W while connecting it to your computer
3. The Pico will appear as a USB drive
4. Drag and drop the MicroPython .uf2 file to the drive
5. The Pico will automatically reboot

### Install Project Files

#### Option 1: Using Thonny IDE

1. Download and install [Thonny IDE](https://thonny.org/)
2. Launch Thonny and select "MicroPython (Raspberry Pi Pico)" in the bottom-right corner
3. Download this project as a ZIP file and extract it
4. In Thonny, use "File > Open" to browse to the extracted project folder
5. Right-click on each file/folder in the project and select "Upload to /"

#### Option 2: Using mpremote

1. Install mpremote: `pip install mpremote`
2. Clone this repository or download and extract the ZIP
3. Navigate to the project directory in a terminal
4. Run: `mpremote cp -r EmbeddedSystems/AudioSink/ :`

## 3. Running the Project

Once the files are uploaded to the Pico W, it will automatically start the BLE Audio Sink application on boot.

### LED Status Indicators

- **Fast blinking** (250ms): Advertising, waiting for BLE connection
- **Slow blinking** (1000ms): Connected to BLE device but no audio data
- **Steady on**: Connected and receiving audio data
- **Off or irregular blinking**: Error state

### Connect from a BLE Audio Source

1. Enable Bluetooth on your phone, tablet, or computer
2. Scan for BLE devices
3. Connect to the device named "Pico-W-Audio"
4. Start playing audio from your device

## 4. Testing

The project includes several test files to verify functionality:

- To run all tests: `import run_tests; run_tests.main()`
- To test only I2S output: `import audio.i2s_driver; audio.i2s_driver.test_i2s_driver()`
- To test only BLE functions: `import ble.ble_core; ble.ble_core.test_ble_audio_sink()`

## 5. Customization

To customize the project, modify `config.py` with your preferred settings:

- Change the device name
- Adjust audio parameters
- Modify pin assignments
- Enable/disable debug output

## 6. Troubleshooting

### No Audio Output
- Check all wiring connections
- Confirm the UDA1334A is powered (LED on the breakout should be lit)
- Verify your speakers/headphones work with another device
- Run the I2S test to verify audio output works independently

### Can't Connect via BLE
- Ensure the Pico W is powered (LED should be blinking)
- Restart your source device's Bluetooth
- Reset the Pico W by pressing the reset button
- Check if the device appears in BLE scanner apps

### Poor Audio Quality
- Increase buffer size in `config.py`
- Reduce distance between BLE source and Pico W
- Check for interference from other wireless devices
- Ensure adequate power supply to the Pico W

## 7. Further Documentation

- [README.md](README.md) - Overall project information
- [README.wiring](README.wiring) - Detailed wiring information
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details 
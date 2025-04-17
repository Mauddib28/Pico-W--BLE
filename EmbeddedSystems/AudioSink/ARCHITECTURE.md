# BLE Audio Sink Architecture

This document outlines the architecture of the BLE Audio Sink project for Raspberry Pi Pico W.

## System Overview

The BLE Audio Sink system enables the Raspberry Pi Pico W to receive audio data over Bluetooth Low Energy (BLE) and play it through an I2S audio interface connected to a UDA1334A DAC.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Raspberry Pi Pico W                        │
│                                                                 │
│  ┌───────────┐      ┌───────────────┐      ┌───────────────┐   │
│  │           │      │               │      │               │   │
│  │  BLE Core ├─────►│  BLE-Audio   ├─────►│  I2S Driver   │   │
│  │           │      │   Adapter     │      │               │   │
│  └───────────┘      └───────────────┘      └───────┬───────┘   │
│        ▲                     ▲                     │           │
│        │                     │                     │           │
│        │                     │                     ▼           │
│  ┌─────┴─────────────────────┴─────────────────────────────┐   │
│  │                     Configuration                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        ▲                                           │
        │                                           │
        │                                           ▼
┌───────┴───────┐                          ┌───────────────┐
│               │                          │               │
│  BLE Source   │                          │   UDA1334A    │
│   Device      │                          │     DAC       │
│               │                          │               │
└───────────────┘                          └───────┬───────┘
                                                   │
                                                   ▼
                                           ┌───────────────┐
                                           │               │
                                           │  Speakers or  │
                                           │  Headphones   │
                                           │               │
                                           └───────────────┘
```

## Component Architecture

### 1. BLE Core (`ble/ble_core.py`)

Responsible for all Bluetooth Low Energy functionality.

**Key Functions:**
- Initializing BLE hardware
- Service and characteristic registration
- Advertisement management
- Connection handling
- Data reception
- Event processing

**Class Structure:**
- `BLEAudioSink`: Main class for BLE functionality
  - Methods for setup, advertising, and event handling
  - Callback registration for audio data, control commands, and status updates

### 2. I2S Driver (`audio/i2s_driver.py`)

Manages the I2S audio output interface to the UDA1334A DAC.

**Key Functions:**
- I2S hardware initialization
- Audio buffer management
- Asynchronous audio playback
- Volume control
- Audio format conversion

**Class Structure:**
- `I2SDriver`: Main class for I2S functionality
  - Methods for initialization, start/stop, and buffer management
  - Asynchronous task for continuous playback

### 3. BLE-Audio Adapter (`audio/ble_audio_adapter.py`)

Connects the BLE input with the I2S output, acting as a bridge between components.

**Key Functions:**
- Audio data processing and forwarding
- Control command interpretation
- Status tracking and reporting
- Buffer management and statistics

**Class Structure:**
- `BLEAudioAdapter`: Main adapter class
  - Initializes both BLE and I2S components
  - Registers callbacks with BLE component
  - Provides methods for starting/stopping the system
  - Handles data flow between components

### 4. Configuration (`config.py`)

Centralized configuration for all system components.

**Key Elements:**
- Hardware pin assignments
- BLE service and characteristic UUIDs
- Audio parameters (sample rate, bit depth, channels)
- BLE advertisement settings
- Command and status codes
- Debug settings

### 5. Main Application (`main.py`)

System entry point and overall application management.

**Key Functions:**
- System initialization
- Background task management
- Status indication via LED
- Memory monitoring
- Error handling

## Data Flow

1. **Audio Data Path:**
   - BLE device sends audio data to the Pico W
   - BLE Core receives data and triggers audio data callback
   - BLE-Audio Adapter processes data and forwards to I2S Driver
   - I2S Driver buffers data and sends to the UDA1334A DAC
   - UDA1334A converts digital data to analog audio

2. **Control Command Path:**
   - BLE device sends control command (play/pause/volume)
   - BLE Core receives command and triggers control callback
   - BLE-Audio Adapter interprets command and controls I2S Driver
   - I2S Driver changes playback state or volume
   - BLE-Audio Adapter updates status

3. **Status Update Path:**
   - System state changes (connected/disconnected/error)
   - BLE-Audio Adapter is notified through callbacks
   - Adapter updates status and triggers visual feedback
   - Status is reported back to connected BLE device

## Asynchronous Processing

The system uses MicroPython's `uasyncio` library for asynchronous operation:

- **Main Loop**: Runs in `main.py` to keep the application alive
- **Background Tasks**:
  - LED status indication task
  - Memory monitoring task
  - I2S playback task
  - Statistics reporting task

This approach allows:
- Non-blocking operations
- Concurrent handling of BLE and I2S operations
- Efficient resource utilization
- Responsive user interface

## Testing Framework

The project includes a comprehensive testing framework:

- **Unit Tests**: Each component has individual test functions
- **Integration Tests**: `run_tests.py` provides full system testing
- **Test Metrics**:
  - Memory usage monitoring
  - Buffer statistics (overruns, packets)
  - Audio quality verification

## Future Enhancements

Potential areas for future development:

1. **Audio Codec Support**: Add support for compressed audio formats (SBC, AAC)
2. **A2DP Protocol**: Implement full A2DP profile for better compatibility
3. **Multiple Connections**: Support for multiple BLE sources
4. **Configuration Interface**: Web or BLE-based configuration portal
5. **Power Management**: Deep sleep modes for battery operation 
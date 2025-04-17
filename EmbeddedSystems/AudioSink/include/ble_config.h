/**
 * ble_config.h - BLE Configuration and Constants
 * 
 * This header file contains configuration settings and constants for the
 * BLE audio sink implementation.
 */

#ifndef BLE_CONFIG_H
#define BLE_CONFIG_H

#include <ArduinoBLE.h>

// BLE Service UUIDs
#define BLE_AUDIO_SERVICE_UUID              "1234" // Custom UUID for Audio Service
#define BLE_MEDIA_CONTROL_SERVICE_UUID      "1235" // Custom UUID for Media Control
#define BLE_VOLUME_CONTROL_SERVICE_UUID     "1236" // Custom UUID for Volume Control
#define BLE_STATUS_SERVICE_UUID             "1237" // Custom UUID for Status Service

// BLE Characteristic UUIDs
#define BLE_AUDIO_DATA_CHAR_UUID            "1238" // Audio data characteristic
#define BLE_MEDIA_CONTROL_CHAR_UUID         "1239" // Media control characteristic
#define BLE_VOLUME_CHAR_UUID                "123A" // Volume control characteristic
#define BLE_STATUS_CHAR_UUID                "123B" // Status characteristic

// L2CAP parameters
#define BLE_L2CAP_PSM                       0x25   // L2CAP PSM value
#define BLE_L2CAP_RX_MTU                    512    // Maximum receive MTU
#define BLE_L2CAP_TX_MTU                    512    // Maximum transmit MTU

// Media control commands
#define MEDIA_CMD_PLAY                      0x01
#define MEDIA_CMD_PAUSE                     0x02
#define MEDIA_CMD_RESUME                    0x03
#define MEDIA_CMD_STOP                      0x04

// Status codes
#define STATUS_IDLE                         0x00
#define STATUS_PLAYING                      0x01
#define STATUS_PAUSED                       0x02
#define STATUS_STOPPED                      0x03
#define STATUS_ERROR                        0xFF

// Function prototypes
void initBLE();
void setupBLEServices();
void advertiseBLEServices();
void handleBLEConnections();
void setupL2CAPChannel();
void handleL2CAPData(uint8_t* data, size_t length);
void sendStatusUpdate(uint8_t status);
void handleMediaControl(uint8_t command);
void handleVolumeControl(uint8_t volume);

// External variables (defined in main)
extern bool isPlaying;
extern uint8_t volume;

#endif // BLE_CONFIG_H 
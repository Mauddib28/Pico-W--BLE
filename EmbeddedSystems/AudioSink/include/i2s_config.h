/**
 * i2s_config.h - I2S Configuration and Constants
 * 
 * This header file contains configuration settings and constants for the
 * I2S audio output implementation.
 */

#ifndef I2S_CONFIG_H
#define I2S_CONFIG_H

#include <I2S.h>

// I2S pin definitions (match those in main.ino)
#define I2S_BCLK_PIN 0      // Bit Clock
#define I2S_LRCLK_PIN 1     // Word/Left-Right Clock  
#define I2S_DATA_PIN 2      // Data pin
#define I2S_MUTE_PIN 3      // Optional mute control (connect to GND to mute)

// I2S configuration
#define SAMPLE_RATE 44100   // Standard CD quality
#define BIT_DEPTH 16        // 16-bit audio
#define AUDIO_CHANNELS 2    // Stereo

// I2S buffer sizes
#define I2S_BUFFER_SIZE 1024  // Output buffer size
#define I2S_QUEUE_SIZE 4      // Number of buffers in the queue

// Function prototypes
void initI2S();
void configureI2SPins();
void startI2S();
void stopI2S();
void muteI2S(bool mute);
void writeAudioData(uint8_t* data, size_t length);
void setI2SVolume(uint8_t volume); // 0-100%
void playTestTone();

// External variables (defined in main)
extern bool isPlaying;
extern uint8_t volume;

#endif // I2S_CONFIG_H 
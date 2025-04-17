/**
 * audio_config.h - Audio Processing Configuration
 * 
 * This header file contains configuration settings and constants for the
 * audio processing implementation.
 */

#ifndef AUDIO_CONFIG_H
#define AUDIO_CONFIG_H

// Audio format configuration
#define AUDIO_FORMAT_PCM      0x01
#define AUDIO_FORMAT_MP3      0x02
#define AUDIO_FORMAT_AAC      0x03

// Audio buffer configuration
#define AUDIO_BUFFER_SIZE     512    // Size of audio buffer in bytes
#define AUDIO_BUFFER_COUNT    4      // Number of audio buffers to use

// Audio playback states
#define PLAYBACK_IDLE         0
#define PLAYBACK_PLAYING      1
#define PLAYBACK_PAUSED       2
#define PLAYBACK_STOPPED      3

// Volume control
#define VOLUME_MIN            0
#define VOLUME_MAX            100
#define VOLUME_DEFAULT        80

// Function prototypes
void initAudioProcessing();
void processAudioPacket(uint8_t* data, size_t length);
void startAudioPlayback();
void pauseAudioPlayback();
void resumeAudioPlayback();
void stopAudioPlayback();
void setAudioVolume(uint8_t volume);
void generateTestTone(uint8_t* buffer, size_t length);

// Audio buffer handling
void pushAudioBuffer(uint8_t* data, size_t length);
bool popAudioBuffer(uint8_t* buffer, size_t* length);
void clearAudioBuffers();

// External variables (defined in main)
extern bool isPlaying;
extern uint8_t volume;
extern uint8_t audioBuffer[];

#endif // AUDIO_CONFIG_H 
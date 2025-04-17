/**
 * serial_interface.h - Serial Command Interface
 * 
 * This header file contains configuration settings and constants for the
 * serial command interface.
 */

#ifndef SERIAL_INTERFACE_H
#define SERIAL_INTERFACE_H

#include <Arduino.h>

// Serial port configuration
#define SERIAL_BAUD_RATE 115200

// Serial command buffer
#define SERIAL_CMD_BUFFER_SIZE 64

// Command identifiers
#define CMD_HELP        "help"
#define CMD_STATUS      "status"
#define CMD_PLAY        "play"
#define CMD_PAUSE       "pause"
#define CMD_RESUME      "resume"
#define CMD_STOP        "stop"
#define CMD_VOLUME      "volume"
#define CMD_NAME        "name"
#define CMD_ALIAS       "alias"
#define CMD_TEST        "test"
#define CMD_INFO        "info"
#define CMD_RESET       "reset"

// Function prototypes
void initSerialInterface();
void processSerialCommands();
void printCommandHelp();
void printSystemStatus();
void handleSerialCommand(char* command);
void executePlayCommand();
void executePauseCommand();
void executeResumeCommand();
void executeStopCommand();
void executeVolumeCommand(int volume);
void executeTestCommand();
void executeInfoCommand();
void executeResetCommand();
void printCommandResult(bool success, const char* message);

// External variables (defined in main)
extern bool isPlaying;
extern uint8_t volume;

#endif // SERIAL_INTERFACE_H 
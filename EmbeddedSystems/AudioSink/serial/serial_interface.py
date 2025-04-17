"""
serial_interface.py - Serial Command Interface

This module contains the implementation of the serial command interface
for controlling the BLE audio sink device.
"""

import sys

# Command identifiers
CMD_HELP = "help"
CMD_STATUS = "status"
CMD_PLAY = "play"
CMD_PAUSE = "pause"
CMD_RESUME = "resume"
CMD_STOP = "stop"
CMD_VOLUME = "volume"
CMD_NAME = "name"
CMD_ALIAS = "alias"
CMD_TEST = "test"
CMD_INFO = "info"
CMD_RESET = "reset"

# Command buffer
cmd_buffer = ""
cmd_ready = False

# External state variables (to be imported from main)
is_playing = None
volume = None

def init_serial_interface():
    """Initialize the serial command interface"""
    global is_playing, volume
    
    # Reference the global variables from main
    from main import is_playing as main_is_playing
    from main import volume as main_volume
    is_playing = main_is_playing
    volume = main_volume
    
    print("Serial interface initialized")
    print_command_help()

def process_serial_commands():
    """Process any pending serial commands"""
    global cmd_buffer, cmd_ready
    
    # Check if any input is available on stdin
    if sys.stdin.readable() and sys.stdin.any():
        char = sys.stdin.read(1)
        
        # Process the character
        if char == '\n' or char == '\r':
            # Command is ready to process
            cmd_ready = True
        else:
            # Add to buffer
            cmd_buffer += char
    
    # Process command if ready
    if cmd_ready:
        command = cmd_buffer.strip()
        cmd_buffer = ""
        cmd_ready = False
        
        # Handle the command
        handle_serial_command(command)

def print_command_help():
    """Print available commands"""
    print("\nAvailable commands:")
    print("  help                  - Show this help")
    print("  status                - Show current status")
    print("  play                  - Start audio playback")
    print("  pause                 - Pause audio playback")
    print("  resume                - Resume audio playback")
    print("  stop                  - Stop audio playback")
    print("  volume <level>        - Set volume (0-100)")
    print("  name                  - Show device name")
    print("  alias                 - Show device alias")
    print("  test                  - Play test tone")
    print("  info                  - Show system info")
    print("  reset                 - Reset the device")
    print("")

def print_system_status():
    """Print current system status"""
    status = "Playing" if is_playing else "Stopped"
    print(f"Status: {status}")
    print(f"Volume: {volume}%")

def handle_serial_command(command):
    """Handle a command received via serial"""
    parts = command.split()
    
    if not parts:
        return
    
    cmd = parts[0].lower()
    
    if cmd == CMD_HELP:
        print_command_help()
    elif cmd == CMD_STATUS:
        print_system_status()
    elif cmd == CMD_PLAY:
        execute_play_command()
    elif cmd == CMD_PAUSE:
        execute_pause_command()
    elif cmd == CMD_RESUME:
        execute_resume_command()
    elif cmd == CMD_STOP:
        execute_stop_command()
    elif cmd == CMD_VOLUME:
        if len(parts) > 1:
            try:
                volume_level = int(parts[1])
                execute_volume_command(volume_level)
            except ValueError:
                print("Error: Volume must be a number between 0-100")
        else:
            print(f"Current volume: {volume}%")
    elif cmd == CMD_NAME:
        from main import BLE_DEVICE_NAME
        print(f"Device name: {BLE_DEVICE_NAME}")
    elif cmd == CMD_ALIAS:
        from main import BLE_DEVICE_ALIAS
        print(f"Device alias: {BLE_DEVICE_ALIAS}")
    elif cmd == CMD_TEST:
        execute_test_command()
    elif cmd == CMD_INFO:
        execute_info_command()
    elif cmd == CMD_RESET:
        execute_reset_command()
    else:
        print(f"Unknown command: {cmd}")
        print("Type 'help' for available commands")

def execute_play_command():
    """Start audio playback"""
    # Call the appropriate audio function
    from audio.audio_config import start_audio_playback
    start_audio_playback()
    print_command_result(True, "Playback started")

def execute_pause_command():
    """Pause audio playback"""
    # Call the appropriate audio function
    from audio.audio_config import pause_audio_playback
    pause_audio_playback()
    print_command_result(True, "Playback paused")

def execute_resume_command():
    """Resume audio playback"""
    # Call the appropriate audio function
    from audio.audio_config import resume_audio_playback
    resume_audio_playback()
    print_command_result(True, "Playback resumed")

def execute_stop_command():
    """Stop audio playback"""
    # Call the appropriate audio function
    from audio.audio_config import stop_audio_playback
    stop_audio_playback()
    print_command_result(True, "Playback stopped")

def execute_volume_command(volume_level):
    """Set volume level"""
    # Call the appropriate audio function
    from audio.audio_config import set_audio_volume
    global volume
    volume = set_audio_volume(volume_level)
    print_command_result(True, f"Volume set to {volume}%")

def execute_test_command():
    """Play test tone"""
    # Generate and play a test tone
    from i2s.i2s_config import play_test_tone
    play_test_tone()
    print_command_result(True, "Playing test tone")

def execute_info_command():
    """Show system information"""
    import os
    import gc
    
    # Get system info
    free_mem = gc.mem_free()
    alloc_mem = gc.mem_alloc()
    total_mem = free_mem + alloc_mem
    
    print("\nSystem Information:")
    print(f"Free memory: {free_mem} bytes")
    print(f"Used memory: {alloc_mem} bytes")
    print(f"Total memory: {total_mem} bytes")
    print(f"Memory usage: {alloc_mem/total_mem*100:.1f}%")
    
    # Show MicroPython version if available
    if hasattr(sys, 'implementation'):
        print(f"MicroPython version: {sys.implementation.version}")
    
    # Show machine info if available
    try:
        import machine
        freq = machine.freq()
        print(f"CPU frequency: {freq/1000000:.0f} MHz")
    except:
        pass

def execute_reset_command():
    """Reset the device"""
    print_command_result(True, "Resetting device...")
    import machine
    machine.reset()

def print_command_result(success, message):
    """Print command result with status indicator"""
    status = "OK" if success else "ERROR"
    print(f"[{status}] {message}") 
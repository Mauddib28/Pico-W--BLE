"""
BLE Audio Adapter

Connects BLE audio input to I2S output.
Handles audio data conversion and buffering.
"""

import uasyncio as asyncio
import struct
import time

from audio.i2s_driver import I2SDriver
from ble.ble_core import BLEAudioSink
from config import (
    I2S_BCK_PIN, I2S_WS_PIN, I2S_SD_PIN,
    AUDIO_SAMPLE_RATE, AUDIO_BIT_DEPTH, AUDIO_CHANNELS, AUDIO_BUFFER_SIZE,
    AUDIO_CHUNK_SIZE, BLE_AUDIO_PACKET_SIZE,
    CMD_PLAY, CMD_PAUSE, STATUS_PLAYING, STATUS_PAUSED
)

class BLEAudioAdapter:
    """
    Adapter that connects BLE audio input to I2S output.
    Handles audio data conversion, buffering, and synchronization.
    """
    
    def __init__(self):
        """Initialize the BLE to I2S adapter."""
        # Create I2S driver
        self.i2s_driver = I2SDriver(
            bck_pin=I2S_BCK_PIN,
            ws_pin=I2S_WS_PIN,
            sd_pin=I2S_SD_PIN,
            sample_rate=AUDIO_SAMPLE_RATE,
            bits=AUDIO_BIT_DEPTH,
            channels=AUDIO_CHANNELS,
            buffer_size=AUDIO_BUFFER_SIZE
        )
        
        # Create BLE audio sink
        self.ble_sink = BLEAudioSink()
        
        # Register callbacks
        self.ble_sink.set_audio_data_callback(self._handle_audio_data)
        self.ble_sink.set_control_callback(self._handle_control_command)
        self.ble_sink.set_status_callback(self._handle_status_update)
        
        # Status tracking
        self.is_running = False
        self.audio_latency = 0
        self.packet_count = 0
        
        # Debug statistics
        self.stats = {
            "packets_received": 0,
            "buffer_overruns": 0,
            "audio_bytes_processed": 0,
            "last_packet_time": 0
        }
    
    async def start(self):
        """Start the BLE audio adapter."""
        if not self.is_running:
            self.is_running = True
            
            # Start I2S playback
            await self.i2s_driver.start()
            
            # Start BLE advertising
            self.ble_sink.start_advertising()
            
            # Start statistics task
            if self.is_running:
                asyncio.create_task(self._stats_task())
            
            print("BLE Audio Adapter started")
    
    async def stop(self):
        """Stop the BLE audio adapter."""
        self.is_running = False
        
        # Stop I2S playback
        await self.i2s_driver.stop()
        
        # Stop BLE
        self.ble_sink.disconnect()
        
        print("BLE Audio Adapter stopped")
    
    def _handle_audio_data(self, data):
        """
        Handle audio data received from BLE.
        
        Args:
            data (bytes): Audio data received via BLE
        """
        if not self.is_running:
            return
        
        # Update statistics
        self.stats["packets_received"] += 1
        self.stats["audio_bytes_processed"] += len(data)
        self.stats["last_packet_time"] = self.ble_sink.get_ticks_ms()
        
        # Create a task to write data to I2S
        asyncio.create_task(self._write_audio_data(data))
    
    async def _write_audio_data(self, data):
        """
        Write audio data to I2S driver.
        
        Args:
            data (bytes): Audio data to write
        """
        # Write data to I2S buffer
        buffer_full = await self.i2s_driver.write(data)
        
        # Track buffer overruns
        if buffer_full:
            self.stats["buffer_overruns"] += 1
    
    def _handle_control_command(self, command):
        """
        Handle control commands received from BLE.
        
        Args:
            command (bytes): Control command data
        """
        if len(command) < 1:
            return
        
        cmd_type = command[0]
        
        # Play/Pause (0x01)
        if cmd_type == CMD_PLAY and len(command) >= 2:
            state = command[1]
            asyncio.create_task(self._handle_play_pause(state))
        
        # Volume (0x02)
        elif cmd_type == 0x02 and len(command) >= 2:
            volume = command[1] / 255.0  # Scale from 0-255 to 0.0-1.0
            self.i2s_driver.set_volume(volume)
            print(f"Volume set to {volume:.2f}")
        
        # Latency adjustment (0x03)
        elif cmd_type == 0x03 and len(command) >= 3:
            latency = struct.unpack('<H', command[1:3])[0]
            self.audio_latency = latency
            print(f"Latency adjustment: {latency}ms")
    
    async def _handle_play_pause(self, state):
        """
        Handle play/pause command.
        
        Args:
            state (int): 0 = pause, 1 = play
        """
        if state == 0:  # Pause
            await self.i2s_driver.stop()
            self.ble_sink.set_status(STATUS_PAUSED)
            print("Playback paused")
        else:  # Play
            await self.i2s_driver.start()
            self.ble_sink.set_status(STATUS_PLAYING)
            print("Playback started")
    
    def _handle_status_update(self, connected):
        """
        Handle BLE connection status updates.
        
        Args:
            connected (bool): Connection status
        """
        if connected:
            print("BLE device connected")
            self._reset_stats()
        else:
            print("BLE device disconnected")
            # Clear audio buffer on disconnect
            self.i2s_driver.clear_buffer()
    
    def _reset_stats(self):
        """Reset the debug statistics."""
        self.stats = {
            "packets_received": 0,
            "buffer_overruns": 0,
            "audio_bytes_processed": 0,
            "last_packet_time": 0
        }
    
    async def _stats_task(self):
        """Task to periodically print statistics."""
        while self.is_running:
            if self.ble_sink.is_connected() and self.stats["packets_received"] > 0:
                print(f"Stats:\nPackets: {self.stats['packets_received']},\nOverruns: {self.stats['buffer_overruns']},\nData: {self.stats['audio_bytes_processed']/1024:.1f}KB")
            await asyncio.sleep(5)


def test_ble_audio_adapter():
    """Test function for BLE audio adapter."""
    adapter = BLEAudioAdapter()
    
    async def run_test():
        await adapter.start()
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Test interrupted")
        finally:
            await adapter.stop()
    
    print("Testing BLE Audio Adapter...")
    asyncio.run(run_test())


if __name__ == "__main__":
    # Run the test
    test_ble_audio_adapter() 
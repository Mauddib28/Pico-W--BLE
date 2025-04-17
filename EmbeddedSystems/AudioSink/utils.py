"""
Utility functions for the BLE Audio Sink application.

This module provides common utility functions including logging,
debugging helpers, and data conversion utilities.
"""

import time
import gc
from micropython import const

# Debug levels
DEBUG_NONE = const(0)
DEBUG_ERROR = const(1)
DEBUG_WARNING = const(2)
DEBUG_INFO = const(3)
DEBUG_DEBUG = const(4)
DEBUG_VERBOSE = const(5)

# Current debug level (can be changed at runtime)
_current_debug_level = DEBUG_INFO

# Debug level names for printing
_DEBUG_NAMES = {
    DEBUG_ERROR: "ERROR",
    DEBUG_WARNING: "WARN",
    DEBUG_INFO: "INFO",
    DEBUG_DEBUG: "DEBUG",
    DEBUG_VERBOSE: "VERBOSE"
}

# Time tracking
_last_time = time.ticks_ms()
_start_time = _last_time


def set_debug_level(level):
    """Set the current debug level."""
    global _current_debug_level
    _current_debug_level = level
    log(DEBUG_INFO, f"Debug level set to {_DEBUG_NAMES.get(level, level)}")


def log(level, message):
    """Log a message at the specified level."""
    if level <= _current_debug_level:
        level_name = _DEBUG_NAMES.get(level, str(level))
        current = time.ticks_ms()
        delta = time.ticks_diff(current, _last_time)
        elapsed = time.ticks_diff(current, _start_time)
        print(f"[{elapsed/1000:.3f}s +{delta/1000:.3f}s] {level_name}: {message}")
        
        # Update last time
        global _last_time
        _last_time = current


def format_bytes(data):
    """Format bytes as a hex string for debugging."""
    if not data:
        return "None"
    if len(data) > 16:
        # If data is too long, only show first and last few bytes
        hex_str = ' '.join([f"{b:02x}" for b in data[:8]])
        hex_str += " ... "
        hex_str += ' '.join([f"{b:02x}" for b in data[-8:]])
        return f"<{len(data)} bytes: {hex_str}>"
    else:
        # Show all bytes
        hex_str = ' '.join([f"{b:02x}" for b in data])
        return f"<{len(data)} bytes: {hex_str}>"


def bytes_to_int(data, signed=False):
    """Convert a bytearray to an integer (little-endian)."""
    result = 0
    for i, b in enumerate(data):
        result += b << (i * 8)
    
    if signed and data[-1] & 0x80:
        # Handle negative values (two's complement)
        result -= (1 << (len(data) * 8))
    
    return result


def int_to_bytes(value, length, signed=False):
    """Convert an integer to a bytearray of specified length (little-endian)."""
    result = bytearray(length)
    for i in range(length):
        result[i] = (value >> (i * 8)) & 0xFF
    return result


def memory_info():
    """Get memory usage information."""
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    percent = alloc / total * 100
    return {
        'free': free,
        'allocated': alloc,
        'total': total,
        'percent_used': percent
    }


def print_memory_info():
    """Print current memory usage."""
    mem = memory_info()
    log(DEBUG_INFO, f"Memory: {mem['allocated']}/{mem['total']} bytes "
               f"({mem['percent_used']:.1f}% used, {mem['free']} free)")


def reset_timer():
    """Reset the elapsed time counter."""
    global _start_time, _last_time
    _start_time = time.ticks_ms()
    _last_time = _start_time
    log(DEBUG_DEBUG, "Timer reset")


def measure_execution_time(func):
    """Decorator to measure execution time of a function."""
    def wrapper(*args, **kwargs):
        start = time.ticks_ms()
        result = func(*args, **kwargs)
        end = time.ticks_ms()
        duration = time.ticks_diff(end, start)
        log(DEBUG_DEBUG, f"{func.__name__} took {duration}ms to execute")
        return result
    return wrapper 
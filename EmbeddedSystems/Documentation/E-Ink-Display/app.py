from flask import Flask, render_template, jsonify
import os
import json

app = Flask(__name__)

# Load code files
CODE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ble_eink_display_demo__basic_bitch.py')

def get_code():
    try:
        with open(CODE_PATH, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Return dummy code if the actual file doesn't exist
        return """# Pico W BLE E-Ink Display Demo
import time
from machine import Pin, SPI
import gc

# BLE Libraries
from micropython import const
import bluetooth
from ble_advertising import advertising_payload

# E-Ink Display Libraries
import framebuf
from epaper import EPD_2in13_V3

# Constants
DEVICE_NAME = "Pico W E-Ink"

# Main Classes and Functions
class BLEEInkDisplay:
    def __init__(self):
        # Initialize hardware
        self.led = Pin("LED", Pin.OUT)
        
        # Initialize E-Ink display
        self.init_display()
        
        # Initialize BLE
        self.init_ble()
    
    def init_display(self):
        # Initialize E-Ink display
        pass
        
    def init_ble(self):
        # Initialize BLE services
        pass

# Main application
def main():
    display = BLEEInkDisplay()
    while True:
        time.sleep(1)
        
if __name__ == "__main__":
    main()
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    """Simple test page for button functionality"""
    return render_template('test.html')

@app.route('/api/code')
def api_code():
    try:
        code = get_code()
        return jsonify({"status": "success", "code": code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/test_fixes')
def test_fixes():
    return render_template('test_fixes.html')

@app.route('/eink_test')
def eink_test():
    return render_template('eink_test.html')

@app.route('/api/services')
def api_services():
    services = {
        "service": {
            "name": "E-Ink Display Service",
            "uuid": "E1234000-A5A5-F5F5-C5C5-111122223333",
            "characteristics": [
                {
                    "name": "Read Buffer",
                    "uuid": "E1234001-A5A5-F5F5-C5C5-111122223333",
                    "properties": ["Read", "Notify"],
                    "description": "Provides the current display state information to connected clients"
                },
                {
                    "name": "Read Status",
                    "uuid": "E1234002-A5A5-F5F5-C5C5-111122223333",
                    "properties": ["Read"],
                    "description": "Indicates the current status of the device"
                },
                {
                    "name": "Write Display",
                    "uuid": "E1234003-A5A5-F5F5-C5C5-111122223333",
                    "properties": ["Write"],
                    "description": "Accepts text that will be displayed on the E-Ink display"
                },
                {
                    "name": "Write Command",
                    "uuid": "E1234004-A5A5-F5F5-C5C5-111122223333",
                    "properties": ["Write"],
                    "description": "Accepts commands to control the display (e.g. clear, refresh)"
                }
            ]
        }
    }
    return jsonify(services)

@app.route('/api/flow')
def api_flow():
    flow = {
        "states": [
            {"id": "boot", "name": "Boot", "description": "Device powers on and initializes"},
            {"id": "init", "name": "Initialize Display", "description": "E-Ink display is initialized"},
            {"id": "testPattern", "name": "Test Pattern", "description": "Display shows test pattern"},
            {"id": "clearDisplay", "name": "Clear Display", "description": "Display is cleared"},
            {"id": "bleReady", "name": "BLE Ready", "description": "Device is ready for BLE connections"},
            {"id": "readyDisplay", "name": "Display Ready", "description": "Shows 'Ready for BLE' on display"},
            {"id": "connected", "name": "Client Connected", "description": "BLE client is connected"},
            {"id": "receiveText", "name": "Receive Text", "description": "Text received from client"},
            {"id": "updateDisplay", "name": "Update Display", "description": "Display updated with received text"},
            {"id": "disconnect", "name": "Client Disconnects", "description": "BLE client disconnects"}
        ],
        "transitions": [
            {"from": "boot", "to": "init"},
            {"from": "init", "to": "testPattern"},
            {"from": "testPattern", "to": "clearDisplay"},
            {"from": "clearDisplay", "to": "bleReady"},
            {"from": "bleReady", "to": "readyDisplay"},
            {"from": "readyDisplay", "to": "connected"},
            {"from": "connected", "to": "receiveText"},
            {"from": "receiveText", "to": "updateDisplay"},
            {"from": "updateDisplay", "to": "connected"},
            {"from": "connected", "to": "disconnect"},
            {"from": "disconnect", "to": "bleReady"}
        ]
    }
    return jsonify(flow)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
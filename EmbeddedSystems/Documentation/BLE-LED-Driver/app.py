from flask import Flask, render_template, jsonify
import os
import json

app = Flask(__name__)

# Load code files
CODE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'AudioController/BLE-LED/main.py')

def get_code():
    """Get the BLE LED Driver code content."""
    try:
        with open(CODE_PATH, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Return error message if file doesn't exist
        return "# ERROR: BLE LED Driver code file not found at expected location."

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/documentation')
def documentation():
    """Documentation page."""
    return render_template('documentation.html')

@app.route('/tutorial')
def tutorial():
    """Tutorial page."""
    return render_template('tutorial.html')

@app.route('/simulator')
def simulator():
    """LED simulator page."""
    return render_template('simulator.html')

@app.route('/api/code')
def api_code():
    """Endpoint to get the code."""
    try:
        code = get_code()
        return jsonify({"status": "success", "code": code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/services')
def api_services():
    """Endpoint to get BLE service structure."""
    services = {
        "service": {
            "name": "LED Service",
            "uuid": "0xA100",
            "characteristics": [
                {
                    "name": "RGB Control",
                    "uuid": "0xA101",
                    "properties": ["Read", "Write"],
                    "description": "Controls the RGB LED color values (RGB format 0-255)"
                },
                {
                    "name": "Status",
                    "uuid": "0xA102",
                    "properties": ["Read", "Notify"],
                    "description": "Provides status information about the LED device"
                }
            ]
        }
    }
    return jsonify(services)

@app.route('/api/flow')
def api_flow():
    """Endpoint to get the BLE state flow."""
    flow = {
        "states": [
            {"id": "init", "name": "Initialize", "description": "BLE stack is activated and services are registered"},
            {"id": "advertising", "name": "Advertising", "description": "Device advertises its LED service"},
            {"id": "connected", "name": "Connected", "description": "Central device is connected"},
            {"id": "receiving", "name": "Receiving Commands", "description": "Processing RGB control commands"},
            {"id": "updating", "name": "Updating LEDs", "description": "Adjusting PWM to control LED colors"},
            {"id": "disconnected", "name": "Disconnected", "description": "Central device disconnects"}
        ],
        "transitions": [
            {"from": "init", "to": "advertising"},
            {"from": "advertising", "to": "connected"},
            {"from": "connected", "to": "receiving"},
            {"from": "receiving", "to": "updating"},
            {"from": "updating", "to": "receiving"},
            {"from": "receiving", "to": "disconnected"},
            {"from": "disconnected", "to": "advertising"}
        ]
    }
    return jsonify(flow)

@app.route('/api/hardware')
def api_hardware():
    """Endpoint to get hardware pin configuration."""
    hardware = {
        "board": "Raspberry Pi Pico W",
        "leds": [
            {"color": "Red", "pin": "GP17", "pwm": True},
            {"color": "Green", "pin": "GP22", "pwm": True},
            {"color": "Blue", "pin": "GP16", "pwm": True}
        ],
        "status_led": {"name": "Onboard LED", "pin": "LED", "function": "Connection indicator"}
    }
    return jsonify(hardware)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
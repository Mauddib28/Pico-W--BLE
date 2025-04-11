#!/usr/bin/env python3
"""
Simple script to run the BLE E-Ink Display documentation web application
without Docker. This will install required dependencies and start the app.
"""

import os
import sys
import subprocess
import webbrowser
import time
import socket
import requests
from pathlib import Path

def check_python_version():
    """Check if Python version is at least 3.6"""
    if sys.version_info < (3, 6):
        print("Python 3.6 or higher is required.")
        sys.exit(1)

def install_dependencies():
    """Install required packages"""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "requests"], 
                             stdout=subprocess.DEVNULL)
        print("All dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install dependencies. Please try running:")
        print("pip install flask requests")
        sys.exit(1)

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    port = start_port
    attempts = 0
    
    # First check if our app might already be running on the default port
    if is_port_in_use(start_port):
        try:
            response = requests.get(f"http://localhost:{start_port}/", timeout=1)
            if response.status_code == 200 and "Pico W BLE" in response.text:
                print(f"An instance of this application appears to be already running on port {start_port}.")
                print(f"You can access it at http://localhost:{start_port}")
                print("To stop the existing server before starting a new one, you can run:")
                print(f"pkill -f \"python.*{start_port}\"")
                choice = input("Do you want to continue and start a new instance on a different port? (y/n): ")
                if choice.lower() != 'y':
                    sys.exit(0)
        except:
            # Not our app or couldn't connect properly, just find another port
            pass
    
    while attempts < max_attempts:
        if not is_port_in_use(port):
            return port
        port += 1
        attempts += 1
        
    print(f"Warning: Could not find an available port after {max_attempts} attempts.")
    return start_port + max_attempts  # Return a port beyond our search range and hope for the best

def test_app(port):
    """Test if the application is responding properly"""
    base_url = f"http://localhost:{port}"
    test_endpoints = [
        "/",
        "/documentation",
        "/tutorial",
        "/api/services",
        "/api/flow",
        "/api/code"
    ]
    
    print("\nTesting application endpoints:")
    all_passed = True
    
    for endpoint in test_endpoints:
        url = base_url + endpoint
        success = False
        retries = 3  # Allow multiple attempts for each endpoint
        
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=5)  # Increased timeout
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                    success = True
                    break
                else:
                    print(f"⚠️ Attempt {attempt+1}/{retries}: {endpoint} - Status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"⚠️ Attempt {attempt+1}/{retries}: {endpoint} - Error: {e}")
                time.sleep(1)  # Wait a bit before retrying
        
        if not success:
            print(f"❌ {endpoint} - Failed after {retries} attempts")
            all_passed = False
    
    if all_passed:
        print("\n✅ All endpoints are working correctly!")
    else:
        print("\n⚠️ Some endpoints failed. The application may not work correctly.")
    
    return all_passed

def run_app():
    """Run the Flask application"""
    try:
        port = find_available_port()
        print(f"Starting the web application on port {port}...")
        
        # Run the Flask app in a separate process
        app_path = Path(__file__).parent / "app.py"
        env = os.environ.copy()
        env["FLASK_APP"] = str(app_path)
        env["FLASK_ENV"] = "development"
        env["FLASK_RUN_PORT"] = str(port)
        env["FLASK_RUN_HOST"] = "0.0.0.0"
        
        # Start the Flask app directly
        flask_process = subprocess.Popen(
            [sys.executable, "-m", "flask", "run"],
            env=env,
            cwd=str(Path(__file__).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the app to start (give it more time)
        print("Waiting for the application to start...")
        for _ in range(20):  # Increase timeout to 10 seconds (20 * 0.5)
            if is_port_in_use(port):
                break
            time.sleep(0.5)
        else:
            print("Error: Application failed to start within the expected time.")
            # Print the error output from the Flask process
            stderr_output = flask_process.stderr.read().decode('utf-8')
            if stderr_output:
                print(f"Flask error output: {stderr_output}")
            flask_process.terminate()
            sys.exit(1)
        
        # Give the app a moment to fully initialize
        time.sleep(2)
        
        # Test if endpoints are working
        app_working = test_app(port)
        
        if app_working:
            # Open browser
            print(f"Opening browser to http://localhost:{port}")
            webbrowser.open(f"http://localhost:{port}")
            
            print("\nPress Ctrl+C to stop the application...")
            
            # Wait for the process to complete or be interrupted
            while True:
                if flask_process.poll() is not None:
                    stderr_output = flask_process.stderr.read().decode('utf-8')
                    if stderr_output:
                        print(f"Flask process ended with error: {stderr_output}")
                    break
                time.sleep(1)
        else:
            flask_process.terminate()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nWeb application stopped.")
    except Exception as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)
    finally:
        # Make sure the Flask process is terminated
        if 'flask_process' in locals() and flask_process.poll() is None:
            flask_process.terminate()
            print("Application process terminated.")

if __name__ == "__main__":
    print("Pico W BLE E-Ink Display Documentation")
    print("======================================")
    
    check_python_version()
    install_dependencies()
    run_app() 
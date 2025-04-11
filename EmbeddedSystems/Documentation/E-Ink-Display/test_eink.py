#!/usr/bin/env python3
import os
import time
import sys
import subprocess
import json
import requests
import webbrowser

try:
    print("Testing E-Ink display functionality...")
    
    # Verify server is running
    response = requests.get("http://localhost:5000/", timeout=5)
    if response.status_code == 200:
        print(f"✅ Server is running on http://localhost:5000/")
    else:
        print(f"❌ Server returned status {response.status_code}")
        sys.exit(1)
    
    # Test test page we created
    response = requests.get("http://localhost:5000/eink_test", timeout=5)
    if response.status_code == 200:
        print(f"✅ E-Ink test page is accessible")
    else:
        print(f"❌ E-Ink test page returned status {response.status_code}")
    
    print("\nTo test the E-Ink display manually, please:") 
    print("1. Open http://localhost:5000/ in your browser")
    print("2. Click the 'E-Ink Display Simulator' button")
    print("3. Enter text in the input field and click 'Send to Display'")
    print("4. Verify that the text appears in the E-Ink display")
    
    # Open browser for user to test
    print("\nOpening browser to http://localhost:5000/eink_test for testing...")
    webbrowser.open("http://localhost:5000/eink_test")
    
    print("\nAlso opening the main page for testing...")
    webbrowser.open("http://localhost:5000/")
    
    print("\nTesting complete!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) 
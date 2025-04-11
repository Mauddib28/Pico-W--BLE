#!/usr/bin/env python3
"""
Verification script to test that the E-Ink display fixes are working correctly.
This script will:
1. Check if the server is running
2. Check if relevant endpoints are accessible
3. Provide instructions for manual verification
"""

import os
import time
import sys
import requests
import webbrowser

def check_server():
    """Check if the server is running and accessible"""
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running at http://localhost:5000/")
            return True
        else:
            print(f"❌ Server returned unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running at http://localhost:5000/")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def check_endpoints():
    """Check if all the relevant endpoints are accessible"""
    endpoints = [
        "/",
        "/documentation",
        "/tutorial",
        "/test_fixes",
        "/eink_test",
        "/api/services",
        "/api/flow",
        "/api/code"
    ]
    
    all_passed = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Endpoint {endpoint} is accessible")
            else:
                print(f"❌ Endpoint {endpoint} returned status code {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error accessing endpoint {endpoint}: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main verification function"""
    print("=" * 60)
    print("E-Ink Display Fix Verification")
    print("=" * 60)
    
    if not check_server():
        print("\nPlease start the server before running this verification script.")
        print("You can start the server by running: python3 run_local.py")
        sys.exit(1)
    
    print("\nChecking endpoints...")
    endpoints_ok = check_endpoints()
    
    if not endpoints_ok:
        print("\nSome endpoints are not accessible. Please check the server logs.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Manual Verification Steps")
    print("=" * 60)
    print("1. Opening the main page at http://localhost:5000/")
    print("2. Click on the 'E-Ink Display Simulator' button in the menu")
    print("3. Enter text in the input field")
    print("4. Click the 'Send to Display' button")
    print("5. Verify that the text appears correctly in the E-Ink display")
    print("\nAlso test the dedicated test page at http://localhost:5000/eink_test")
    print("=" * 60)
    
    # Open both pages for testing
    print("\nOpening browsers for testing...")
    webbrowser.open("http://localhost:5000/")
    time.sleep(1)
    webbrowser.open("http://localhost:5000/eink_test")
    
    print("\nVerification complete! Please perform the manual verification steps.")
    print("If everything works correctly, the E-Ink display issue has been fixed.")

if __name__ == "__main__":
    main() 
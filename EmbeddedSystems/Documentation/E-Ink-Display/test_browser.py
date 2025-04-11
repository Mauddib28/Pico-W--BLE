#!/usr/bin/env python3
import os
import time
import http.client
import json

def test_connection():
    """Test if the server is running"""
    try:
        conn = http.client.HTTPConnection("localhost", 5000)
        conn.request("GET", "/")
        response = conn.getresponse()
        return response.status == 200
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return False

def test_api_endpoints():
    """Test if the API endpoints return valid JSON"""
    endpoints = [
        "/api/services",
        "/api/flow",
        "/api/code"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            conn = http.client.HTTPConnection("localhost", 5000)
            conn.request("GET", endpoint)
            response = conn.getresponse()
            
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data:
                    results[endpoint] = "✅ Returns valid JSON"
                else:
                    results[endpoint] = "❌ Returns empty JSON"
            else:
                results[endpoint] = f"❌ Returns status code {response.status}"
        except Exception as e:
            results[endpoint] = f"❌ Error: {e}"
    
    return results

def main():
    """Main test function"""
    print("Testing browser rendering...")
    
    # Check if server is running
    if not test_connection():
        print("❌ Server is not running at http://localhost:5000")
        return
    
    print("✅ Server is running at http://localhost:5000")
    
    # Test API endpoints
    api_results = test_api_endpoints()
    for endpoint, result in api_results.items():
        print(f"{endpoint}: {result}")
    
    print("\nBrowser rendering tests:")
    print("For full browser testing, please open http://localhost:5000 in your browser and check:")
    print("1. The BLE Service Structure diagram is visible and properly formatted")
    print("2. The BLE State Flow diagram is visible and properly formatted")
    print("3. The E-Ink display simulator shows text when updated")
    
    print("\nManual verification required for complete browser rendering tests.")

if __name__ == "__main__":
    main() 
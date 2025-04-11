#!/bin/bash

echo "Testing website functionality..."

# Test main page
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
if [ "$response" = "200" ]; then
    echo "✅ Main page (/) is accessible"
else
    echo "❌ Main page (/) returned status code $response"
fi

# Test documentation page
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/documentation)
if [ "$response" = "200" ]; then
    echo "✅ Documentation page (/documentation) is accessible"
else
    echo "❌ Documentation page (/documentation) returned status code $response"
fi

# Test tutorial page
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/tutorial)
if [ "$response" = "200" ]; then
    echo "✅ Tutorial page (/tutorial) is accessible"
else
    echo "❌ Tutorial page (/tutorial) returned status code $response"
fi

# Test API endpoints
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/services)
if [ "$response" = "200" ]; then
    echo "✅ Services API (/api/services) is working"
else
    echo "❌ Services API (/api/services) returned status code $response"
fi

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/flow)
if [ "$response" = "200" ]; then
    echo "✅ Flow API (/api/flow) is working"
else
    echo "❌ Flow API (/api/flow) returned status code $response"
fi

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/code)
if [ "$response" = "200" ]; then
    echo "✅ Code API (/api/code) is working"
else
    echo "❌ Code API (/api/code) returned status code $response"
fi

echo "All tests completed!" 
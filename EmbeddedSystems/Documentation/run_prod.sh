#!/bin/bash

# Production run script for the BLE E-Ink Display Documentation
# This script runs the application in production mode without debug tools

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Create production docker-compose file
cat > docker-compose.prod.yml << EOL
version: '3'

services:
  web:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "5000:5000"
    volumes:
      - ..:/app/parent_dir
    environment:
      - FLASK_APP=app.py
      - FLASK_ENV=production
      - PRODUCTION=1
EOL

# Create production Dockerfile
cat > Dockerfile.prod << EOL
FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir flask gunicorn

# Copy production index.html without debug tools
RUN sed '/debug.js/d' /app/templates/index.html > /app/templates/index.html.prod && \
    mv /app/templates/index.html.prod /app/templates/index.html

EXPOSE 5000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
EOL

echo "Starting Pico W BLE E-Ink Display Documentation Web Application in PRODUCTION mode..."
echo "This may take a minute to build on first run."

# Build and start the Docker container
docker-compose -f docker-compose.prod.yml up --build

# When the container stops
echo "Web application stopped." 
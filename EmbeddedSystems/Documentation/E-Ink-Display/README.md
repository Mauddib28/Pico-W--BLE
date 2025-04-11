# Pico W BLE E-Ink Display Documentation

This interactive documentation helps you understand the Raspberry Pi Pico W BLE E-Ink Display project. The web application provides:

- Interactive visualization of the GATT service structure
- E-Ink display simulator
- Code walkthrough with syntax highlighting
- BLE state machine flow visualization
- Comprehensive documentation and tutorial

## Running the Application

There are two ways to run this application:

### Option 1: Using Docker (Recommended)

If you have Docker and Docker Compose installed:

1. Open a terminal in this directory
2. Make the run script executable: `chmod +x run.sh`
3. Run the application: `./run.sh`
4. Open your browser to: http://localhost:5000

This method is recommended as it ensures all dependencies are automatically handled.

### Option 2: Running Locally

If you prefer not to use Docker:

1. Ensure you have Python 3.6+ installed
2. Run: `python3 run_local.py`
3. Your browser should automatically open to http://localhost:5000

## Application Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
- `static/`: CSS and JavaScript files
- `Dockerfile` & `docker-compose.yml`: Docker configuration
- `run.sh`: Docker run script
- `run_local.py`: Python run script

## Features

- **Home Page**: Overview with three main sections
  - BLE Service Structure: Visualizes the GATT hierarchy
  - E-Ink Display Simulator: Simulates how the physical display works
  - Code Walkthrough: Explore the Python code with syntax highlighting

- **Tutorial**: Step-by-step walkthrough of the code and concepts
  - Explains BLE fundamentals
  - Details E-Ink display operation
  - Breakdowns key code sections

- **Documentation**: Comprehensive reference
  - Hardware components
  - BLE service details
  - Code structure
  - Improvement suggestions

## Requirements

- For Docker method: Docker and Docker Compose
- For local method: Python 3.6+ and Flask

## Source Code

The original source code being documented is located at:
`../ble_eink_display_demo__basic_bitch.py` 
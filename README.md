# Light Box Controller

A MicroPython-based web interface for controlling the Pimoroni Plasma 2350 W LED driver board. This project provides a user-friendly web interface to control individual and groups of LEDs, with persistence of LED states across power cycles.

## Features

- Web-based control interface
- Individual LED control
- Global LED control
- Color picker for precise color selection
- Brightness control
- State persistence across power cycles
- Responsive design for mobile and desktop
- Error handling

## Hardware Requirements

- Pimoroni Plasma 2350 W LED driver board
- WS2812 or APA102 LED strip
- Power supply (5V, 3A minimum recommended)

## Software Requirements

- MicroPython 1.20.0 or later
- Required Python packages (see requirements.txt):
  - phew
  - plasma

## Installation

1. Flash latest MicroPython to your Pimoroni Plasma 2350 W
2. Copy the project files to the Pico:
   - `main.py`
   - `requirements.txt`
   - `templates/`
     - `index.html`
     - `404.html`
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Power on the device
2. Connect to the WiFi access point:
   - SSID: LightBox
   - Password: test
3. Open a web browser and navigate to:
   - http://192.168.4.1 (default IP address)
4. Use the web interface to:
   - Select individual LEDs by clicking on them
   - Adjust color using the color picker
   - Control brightness using the slider
   - Apply changes to all LEDs using the global controls

## File Structure

```
.
├── main.py              # Main application code
├── requirements.txt     # Python package dependencies
├── README.md           # This file
└── templates/          # Web interface templates
    ├── index.html      # Main control interface
    └── 404.html        # Custom error page
```

## LED State Persistence

LED states are automatically saved to a JSON file (`led_states.json`) after each change. The states are restored when the device is powered on, ensuring your LED configuration persists across power cycles.

## License

MIT - see the header in `main.py` for details.

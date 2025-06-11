"""
File: main.py
Target Device: Pimoroni Plasma 2350 W LED driver board
Language: MicroPython 1.20.0
Author: Guy Turner

MIT License

Copyright (c) 2024 Guy Turner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Description:
This script implements a web-based control interface for the Pimoroni Plasma 2350 W LED driver board.
It provides functionality for controlling individual and groups of LEDs, with persistence of LED states
across power cycles. The interface is served via a WiFi access point and can be accessed through a web browser.
"""

import plasma
from plasma import plasma_stick
import phew
from phew import server, access_point, get_ip_address
from phew.template import render_template
import time
import json
import os

# WiFi configuration
WIFI_SSID = "LightBox"
WIFI_PASSWORD = "test"

# LED strip configuration
LED_COUNT = 30
LED_TYPE = "WS2812"  # or "APA102" depending on your strip type
LED_STATE_FILE = "led_states.json"

# Initialize Plasma
plasma_stick = plasma_stick.PlasmaStick()
plasma_stick.set_led_count(LED_COUNT)

# Initialize the LED strip
if LED_TYPE == "WS2812":
    led_strip = plasma.WS2812(LED_COUNT, 0, 0, plasma_stick)
else:
    led_strip = plasma.APA102(LED_COUNT, 0, 0, plasma_stick)

def load_led_states():
    """Load LED states from file or create default states if file doesn't exist."""
    try:
        if LED_STATE_FILE in os.listdir():
            with open(LED_STATE_FILE, 'r') as f:
                states = json.load(f)
                # Validate the loaded states
                if len(states) == LED_COUNT and all(
                    isinstance(state, dict) and 
                    'color' in state and 
                    'brightness' in state 
                    for state in states
                ):
                    return states
    except Exception as e:
        print(f"Error loading LED states: {e}")
    
    # Return default states if file doesn't exist or is invalid
    return [{"color": "#000000", "brightness": 100} for _ in range(LED_COUNT)]

def save_led_states(states):
    """Save LED states to file."""
    try:
        with open(LED_STATE_FILE, 'w') as f:
            json.dump(states, f)
    except Exception as e:
        print(f"Error saving LED states: {e}")

# Load initial LED states
led_states = load_led_states()

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def apply_brightness(rgb, brightness):
    """Apply brightness to RGB values."""
    return tuple(int(c * brightness / 100) for c in rgb)

def update_led(index, color, brightness):
    """Update a single LED with color and brightness."""
    rgb = hex_to_rgb(color)
    rgb = apply_brightness(rgb, brightness)
    led_strip.set_rgb(index, *rgb)
    led_states[index] = {"color": color, "brightness": brightness}
    save_led_states(led_states)  # Save after each update

def update_all_leds(color, brightness):
    """Update all LEDs with the same color and brightness."""
    for i in range(LED_COUNT):
        update_led(i, color, brightness)
    save_led_states(led_states)  # Save after bulk update

def restore_led_states():
    """Restore all LEDs to their saved states."""
    for i, state in enumerate(led_states):
        rgb = hex_to_rgb(state['color'])
        rgb = apply_brightness(rgb, state['brightness'])
        led_strip.set_rgb(i, *rgb)

# Web server routes
@server.route("/", ["GET"])
async def index(request):
    return await render_template("index.html", led_count=LED_COUNT, led_states=led_states)

@server.route("/update_led", ["POST"])
def update_led_route(request):
    try:
        data = json.loads(request.body)
        index = data.get("index")
        color = data.get("color")
        brightness = int(data.get("brightness"))
        
        if 0 <= index < LED_COUNT:
            update_led(index, color, brightness)
            return phew.Response("OK", content_type="text/plain")
        else:
            return phew.Response("Invalid LED index", status=400)
    except Exception as e:
        return phew.Response(f"Error: {str(e)}", status=400)

@server.route("/update_global", ["POST"])
def update_global_route(request):
    try:
        data = json.loads(request.body)
        color = data.get("color")
        brightness = int(data.get("brightness"))
        
        update_all_leds(color, brightness)
        return phew.Response("OK", content_type="text/plain")
    except Exception as e:
        return phew.Response(f"Error: {str(e)}", status=400)

# Catchall route for 404 errors
@server.catchall()
async def catchall(request):
    return await render_template("404.html", status=404)

def main():
    # Restore LED states from saved configuration
    restore_led_states()
    
    # Create access point
    print("Starting access point...")
    access_point(WIFI_SSID, WIFI_PASSWORD)
    ip = get_ip_address()
    print(f"Access point started. IP address: {ip}")
    
    # Start the web server
    print("Starting web server...")
    server.run(host="0.0.0.0", port=80)

if __name__ == "__main__":
    main()

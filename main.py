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
across power cycles. The interface is served via a WiFi access point and can be accessed through a web
browser.
"""

import json
import os
import network

import plasma
from phew import server, access_point
from phew.template import render_template

# WiFi configuration
WIFI_SSID = "LightBox"
WIFI_PASSWORD = "lightboxpassword"

# LED strip configuration
LED_COUNT = 30
LED_TYPE = "WS2812"  # or "APA102" depending on your strip type
LED_STATE_FILE = "led_states.json"


# Initialize the LED strip
if LED_TYPE == "WS2812":
    led_strip = plasma.WS2812(LED_COUNT, 0, 0)
else:
    led_strip = plasma.APA102(LED_COUNT, 0, 0)


def load_led_states():
    """Load LED states from file or create default states if file doesn't exist."""
    # Create default states
    default_states = [{"color": "#FF0000", "brightness": 100} for _ in range(LED_COUNT)]
    
    # Check if file exists
    if LED_STATE_FILE not in os.listdir():
        save_led_states(default_states)
        return default_states
        
    # Try to load and validate states from file
    try:
        with open(LED_STATE_FILE, 'r', encoding='utf-8') as f:
            states = json.load(f)
            # Validate the loaded states
            if (len(states) == LED_COUNT and all(
                isinstance(state, dict) and
                'color' in state and
                'brightness' in state
                for state in states
            )):
                return states
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading LED states: {e}")
    
    # If file exists but is invalid, save and return default states
    save_led_states(default_states)
    return default_states

def save_led_states(states):
    """Save LED states to file."""
    try:
        with open(LED_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(states, f)
    except IOError as e:
        print(f"Error saving LED states: {e}")

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def apply_brightness(rgb, brightness):
    """Apply brightness to RGB values."""
    return tuple(int(c * brightness / 100) for c in rgb)

def update_led(index, color, brightness):
    """Update a single LED with color and brightness."""
    global led_states, led_strip
    rgb = hex_to_rgb(color)
    rgb = apply_brightness(rgb, brightness)
    led_strip.set_rgb(index, *rgb)
    led_states[index] = {"color": color, "brightness": brightness}
    save_led_states(led_states)

def update_all_leds(color, brightness):
    """Update all LEDs with the same color and brightness."""
    global led_states
    for i in range(LED_COUNT):
        update_led(i, color, brightness)
    save_led_states(led_states)

def restore_led_states():
    """Restore all LEDs to their saved states."""
    global led_states, led_strip
    for i, state in enumerate(led_states):
        rgb = hex_to_rgb(state['color'])
        rgb = apply_brightness(rgb, state['brightness'])
        led_strip.set_rgb(i, *rgb)

@server.route("/", ["GET"])
async def index(request):
    """Serve the main control interface."""
    #return await render_template("index.html", name="GT")
    return await render_template("templates/index.html", led_count=LED_COUNT, led_states=led_states)


@server.route("/update_led", ["POST"])
def update_led_route(request):
    """Handle individual LED update requests."""
    try:
        data = json.loads(request.body)
        led_index = data.get("index")
        color = data.get("color")
        brightness = int(data.get("brightness"))
        
        if 0 <= led_index < LED_COUNT:
            update_led(led_index, color, brightness)
            return "OK", 200, "text/html"
        return "Invalid LED index", 400, "text/html"
    except (ValueError, json.JSONDecodeError) as e:
        return f"Error: {str(e)}", 400, "text/html"

@server.route("/update_global", ["POST"])
def update_global_route(request):
    """Handle global LED update requests."""
    try:
        data = json.loads(request.body)
        color = data.get("color")
        brightness = int(data.get("brightness"))
        
        update_all_leds(color, brightness)
        return "OK", 200, "text/html"
    except (ValueError, json.JSONDecodeError) as e:
        return f"Error: {str(e)}", 400, "text/html"


@server.catchall()
def catchall(request):
    """Handle 404 errors."""
    return await render_template("templates/404.html", status=404)


# Start 
led_strip.start()

# Load initial LED states
led_states = load_led_states()

# Restore LED states from saved configuration
restore_led_states()

# Create access point
print("Starting access point...")
access_point(WIFI_SSID, WIFI_PASSWORD)
ip = network.WLAN(network.STA_IF).ifconfig()[0]
print(f"Access point started. IP address: {ip}")

# Start the web server
print("Starting web server...")
server.run()


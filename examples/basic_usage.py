#!/usr/bin/env python3
"""
Basic usage example for Arduino Mouse Proxy.

Make sure the Arduino Leonardo is connected and flashed with mouse_proxy firmware.
Adjust the port to match your system (e.g., "/dev/ttyACM0" on Linux, "COM3" on Windows).
"""

import sys
import time

# Add parent directory to path for local development
sys.path.insert(0, "../python")

from arduino_mouse import ArduinoMouse, Curve


def main():
    # Adjust port as needed for your system
    port = "/dev/ttyACM0"

    print(f"Connecting to Arduino on {port}...")

    with ArduinoMouse(port=port) as mouse:
        print("Connected! Starting mouse movement demo...")
        print("(Move your eyes to the mouse cursor to see the effect)")
        time.sleep(1)

        # Draw a square with LINEAR movement
        print("\n1. Drawing a square (LINEAR curve)...")
        mouse.move(dx=200, dy=0, duration_ms=500, curve=Curve.LINEAR)
        mouse.move(dx=0, dy=200, duration_ms=500, curve=Curve.LINEAR)
        mouse.move(dx=-200, dy=0, duration_ms=500, curve=Curve.LINEAR)
        mouse.move(dx=0, dy=-200, duration_ms=500, curve=Curve.LINEAR)

        time.sleep(1)

        # Smooth diagonal movement with EASE_IN_OUT
        print("\n2. Smooth diagonal movement (EASE_IN_OUT curve)...")
        mouse.move(dx=300, dy=150, duration_ms=1000, curve=Curve.EASE_IN_OUT)

        time.sleep(0.5)

        # Quick snap back with EASE_OUT
        print("\n3. Quick return (EASE_OUT curve)...")
        mouse.move(dx=-300, dy=-150, duration_ms=400, curve=Curve.EASE_OUT)

        time.sleep(1)

        # Slow start movement with EASE_IN
        print("\n4. Slow start movement (EASE_IN curve)...")
        mouse.move(dx=100, dy=-100, duration_ms=800, curve=Curve.EASE_IN)

        print("\nDemo complete!")


if __name__ == "__main__":
    main()

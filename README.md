# Arduino Mouse Proxy

Control mouse movements programmatically through an Arduino Leonardo acting as a USB HID mouse.

## Requirements

- Arduino Leonardo (or other board with native USB HID support)
- Python 3.7+
- `pyserial`

## Setup

### Arduino

Flash `arduino/mouse_proxy/mouse_proxy.ino` to your Leonardo using Arduino IDE or:

```bash
arduino-cli compile --fqbn arduino:avr:leonardo arduino/mouse_proxy
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo arduino/mouse_proxy
```

### Python

```bash
pip install git+https://github.com/dzmitry-savitski/arduino-mouse-proxy.git
```

Or add to `requirements.txt`:
```
arduino-mouse @ git+https://github.com/dzmitry-savitski/arduino-mouse-proxy.git
```

## Usage

```python
from arduino_mouse import ArduinoMouse, Curve

with ArduinoMouse(port="/dev/ttyACM0") as mouse:
    # Move 100px right, 50px up over 500ms
    mouse.move(dx=100, dy=-50, duration_ms=500)

    # Smooth movement with easing
    mouse.move(dx=200, dy=100, duration_ms=1000, curve=Curve.EASE_IN_OUT)
```

### Available Curves

- `Curve.LINEAR` - Constant speed
- `Curve.EASE_IN` - Accelerates from start
- `Curve.EASE_OUT` - Decelerates to end
- `Curve.EASE_IN_OUT` - Smooth acceleration and deceleration

## How It Works

1. Python sends movement commands (dx, dy, duration, curve) via serial
2. Arduino interpolates the movement over the specified duration
3. Arduino sends ACK when movement completes
4. Python's `move()` method blocks until ACK is received

See [spec.md](spec.md) for protocol details.

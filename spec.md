# Arduino Mouse Proxy - Specification

## Overview

A system that allows Python to control mouse movements through an Arduino Leonardo acting as a USB HID mouse device. The Arduino appears as a native mouse to the operating system, enabling programmatic mouse control that bypasses software-level input restrictions.

## Architecture

```
┌─────────────────┐     Serial      ┌─────────────────┐     USB HID     ┌──────────┐
│  Python Client  │ ──────────────► │ Arduino Leonardo │ ─────────────► │    PC    │
│                 │ ◄────────────── │   (Mouse HID)    │                │  (Host)  │
└─────────────────┘   ACK response  └─────────────────┘                └──────────┘
```

## Components

### 1. Python Library (`arduino_mouse`)

**Interface:**
```python
from arduino_mouse import ArduinoMouse, Curve

mouse = ArduinoMouse(port="/dev/ttyACM0", baudrate=115200)

# Move mouse relatively: dx, dy in pixels, duration in milliseconds
# Blocks until movement completes
mouse.move(dx=100, dy=-50, duration_ms=500, curve=Curve.LINEAR)

# Available curves
Curve.LINEAR      # Constant speed
Curve.EASE_IN     # Accelerates from start
Curve.EASE_OUT    # Decelerates to end
Curve.EASE_IN_OUT # Smooth acceleration and deceleration

mouse.close()
```

**Behavior:**
- `move()` is synchronous/blocking - returns only after Arduino confirms completion
- Raises `TimeoutError` if ACK not received within `duration_ms + timeout_buffer`
- Raises `ConnectionError` if serial port unavailable

### 2. Serial Protocol

**Command Format (Python → Arduino):**
```
[START][CMD][DX_LO][DX_HI][DY_LO][DY_HI][DUR_LO][DUR_HI][CURVE][CHECKSUM]
```

| Field     | Size   | Description                              |
|-----------|--------|------------------------------------------|
| START     | 1 byte | Magic byte `0xAA`                        |
| CMD       | 1 byte | Command type: `0x01` = MOVE              |
| DX        | 2 bytes| Signed 16-bit, little-endian, pixels     |
| DY        | 2 bytes| Signed 16-bit, little-endian, pixels     |
| DURATION  | 2 bytes| Unsigned 16-bit, little-endian, ms       |
| CURVE     | 1 byte | 0=LINEAR, 1=EASE_IN, 2=EASE_OUT, 3=EASE_IN_OUT |
| CHECKSUM  | 1 byte | XOR of all preceding bytes               |

**Response Format (Arduino → Python):**
```
[RESP_CODE]
```

| Code | Meaning                    |
|------|----------------------------|
| 0x00 | ACK - Movement completed   |
| 0x01 | NAK - Checksum error       |
| 0x02 | NAK - Invalid command      |
| 0x03 | NAK - Movement interrupted |

### 3. Arduino Firmware

**Features:**
- Uses Arduino Mouse library for HID functionality
- Executes smooth interpolated movement over specified duration
- Supports configurable easing curves
- Single movement at a time (new command interrupts current, sends NAK 0x03)
- Sends ACK when movement completes

**Movement Interpolation:**
- Update rate: ~100 Hz (10ms intervals)
- Calculates position delta based on elapsed time and selected curve
- Handles sub-pixel accumulation to ensure total movement matches request

**Easing Functions:**
- LINEAR: `t`
- EASE_IN: `t²`
- EASE_OUT: `1 - (1-t)²`
- EASE_IN_OUT: `t < 0.5 ? 2t² : 1 - (-2t+2)²/2`

Where `t` is normalized time [0, 1].

## Constraints

| Parameter       | Min   | Max     | Notes                              |
|-----------------|-------|---------|-------------------------------------|
| dx, dy          | -32768| 32767   | Signed 16-bit range                |
| duration_ms     | 1     | 65535   | Unsigned 16-bit, practical max ~10s|
| Serial baudrate | -     | 115200  | Fixed for reliability              |

## Error Handling

| Scenario                  | Python Behavior                      | Arduino Behavior           |
|---------------------------|--------------------------------------|----------------------------|
| Serial disconnected       | Raise `ConnectionError`              | N/A                        |
| Checksum mismatch         | Retry once, then raise `ProtocolError` | Send NAK 0x01            |
| ACK timeout               | Raise `TimeoutError`                 | N/A                        |
| New command during move   | N/A (blocking)                       | Stop current, NAK 0x03, start new |
| Invalid curve value       | Raise `ValueError` before sending    | Send NAK 0x02              |

## File Structure

```
arduino-mouse-proxy/
├── spec.md                    # This specification
├── arduino/
│   └── mouse_proxy/
│       └── mouse_proxy.ino    # Arduino firmware
├── python/
│   └── arduino_mouse/
│       ├── __init__.py
│       ├── client.py          # ArduinoMouse class
│       ├── protocol.py        # Message encoding/decoding
│       └── curves.py          # Curve enum and functions
├── examples/
│   └── basic_usage.py
└── README.md
```

## Testing Strategy

1. **Arduino standalone**: Serial monitor to send raw bytes, verify HID movement
2. **Protocol test**: Python sends commands, verify ACK responses
3. **Integration test**: Full movement test with visual verification
4. **Edge cases**: Max values, zero duration, rapid successive commands

## Dependencies

**Python:**
- `pyserial` - Serial communication

**Arduino:**
- `Mouse.h` - Built-in Arduino Leonardo HID library

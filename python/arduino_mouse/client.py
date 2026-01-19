"""
Arduino Mouse Proxy client for controlling mouse movements via Arduino Leonardo.
"""

import serial
from typing import Optional

from .curves import Curve
from .protocol import (
    encode_move_command,
    decode_response,
    response_code_to_string,
    ProtocolError,
    ACK_OK,
    NAK_CHECKSUM,
)


class ArduinoMouse:
    """
    Client for controlling mouse movements through an Arduino Leonardo.

    The Arduino must be flashed with the mouse_proxy firmware and connected
    via USB serial port.

    Example:
        mouse = ArduinoMouse(port="/dev/ttyACM0")
        mouse.move(dx=100, dy=-50, duration_ms=500)
        mouse.close()

    Or using context manager:
        with ArduinoMouse(port="/dev/ttyACM0") as mouse:
            mouse.move(dx=100, dy=-50, duration_ms=500)
    """

    DEFAULT_BAUDRATE = 115200
    DEFAULT_TIMEOUT_BUFFER_MS = 1000
    MAX_RETRIES = 1

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout_buffer_ms: int = DEFAULT_TIMEOUT_BUFFER_MS,
    ):
        """
        Initialize connection to Arduino.

        Args:
            port: Serial port path (e.g., "/dev/ttyACM0" or "COM3")
            baudrate: Serial baudrate (default 115200)
            timeout_buffer_ms: Extra time to wait for ACK beyond movement duration
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout_buffer_ms = timeout_buffer_ms
        self._serial: Optional[serial.Serial] = None
        self._connect()

    def _connect(self) -> None:
        """Establish serial connection."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
            )
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to Arduino on {self.port}: {e}")

    def _ensure_connected(self) -> None:
        """Ensure serial connection is active."""
        if self._serial is None or not self._serial.is_open:
            raise ConnectionError("Not connected to Arduino")

    def move(
        self,
        dx: int,
        dy: int,
        duration_ms: int,
        curve: Curve = Curve.LINEAR,
    ) -> None:
        """
        Move mouse relative to current position.

        This method blocks until the Arduino confirms the movement is complete.

        Args:
            dx: Horizontal movement in pixels (positive = right, negative = left)
            dy: Vertical movement in pixels (positive = down, negative = up)
            duration_ms: Duration of movement in milliseconds
            curve: Easing curve for the movement (default LINEAR)

        Raises:
            ValueError: If parameters are out of valid range
            ConnectionError: If serial connection is lost
            TimeoutError: If Arduino doesn't respond in time
            ProtocolError: If communication protocol fails
        """
        self._ensure_connected()

        # Validate curve
        if not isinstance(curve, Curve):
            try:
                curve = Curve(curve)
            except ValueError:
                raise ValueError(f"Invalid curve value: {curve}")

        # Encode command
        command = encode_move_command(dx, dy, duration_ms, int(curve))

        # Calculate timeout
        timeout_seconds = (duration_ms + self.timeout_buffer_ms) / 1000.0

        # Send with retry on checksum error
        for attempt in range(self.MAX_RETRIES + 1):
            # Clear any pending data
            self._serial.reset_input_buffer()

            # Send command
            self._serial.write(command)
            self._serial.flush()

            # Wait for response
            self._serial.timeout = timeout_seconds
            response = self._serial.read(1)

            if len(response) == 0:
                raise TimeoutError(
                    f"Arduino did not respond within {timeout_seconds:.1f}s"
                )

            success, code = decode_response(response)

            if success:
                return

            # Handle errors
            if code == NAK_CHECKSUM and attempt < self.MAX_RETRIES:
                continue  # Retry on checksum error

            raise ProtocolError(
                f"Movement failed: {response_code_to_string(code)}"
            )

    def close(self) -> None:
        """Close the serial connection."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            self._serial = None

    def __enter__(self) -> "ArduinoMouse":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure connection is closed."""
        self.close()

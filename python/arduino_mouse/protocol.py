"""
Serial protocol encoding/decoding for Arduino Mouse Proxy.
"""

import struct
from typing import Tuple

# Protocol constants
START_BYTE = 0xAA
CMD_MOVE = 0x01
PACKET_SIZE = 10

# Response codes
ACK_OK = 0x00
NAK_CHECKSUM = 0x01
NAK_INVALID = 0x02
NAK_INTERRUPTED = 0x03


class ProtocolError(Exception):
    """Raised when protocol communication fails."""
    pass


def encode_move_command(dx: int, dy: int, duration_ms: int, curve: int) -> bytes:
    """
    Encode a move command into bytes for serial transmission.

    Args:
        dx: Horizontal movement in pixels (-32768 to 32767)
        dy: Vertical movement in pixels (-32768 to 32767)
        duration_ms: Movement duration in milliseconds (1 to 65535)
        curve: Easing curve type (0-3)

    Returns:
        10-byte command packet
    """
    if not -32768 <= dx <= 32767:
        raise ValueError(f"dx must be in range [-32768, 32767], got {dx}")
    if not -32768 <= dy <= 32767:
        raise ValueError(f"dy must be in range [-32768, 32767], got {dy}")
    if not 1 <= duration_ms <= 65535:
        raise ValueError(f"duration_ms must be in range [1, 65535], got {duration_ms}")
    if not 0 <= curve <= 3:
        raise ValueError(f"curve must be in range [0, 3], got {curve}")

    # Pack: start, cmd, dx (2 bytes LE), dy (2 bytes LE), duration (2 bytes LE), curve
    packet = struct.pack('<BBhhHB', START_BYTE, CMD_MOVE, dx, dy, duration_ms, curve)

    # Calculate XOR checksum
    checksum = 0
    for byte in packet:
        checksum ^= byte

    return packet + bytes([checksum])


def decode_response(response: bytes) -> Tuple[bool, int]:
    """
    Decode a response from the Arduino.

    Args:
        response: Single byte response

    Returns:
        Tuple of (success: bool, code: int)
    """
    if len(response) != 1:
        raise ProtocolError(f"Expected 1-byte response, got {len(response)} bytes")

    code = response[0]
    success = code == ACK_OK
    return success, code


def response_code_to_string(code: int) -> str:
    """Convert response code to human-readable string."""
    messages = {
        ACK_OK: "Movement completed successfully",
        NAK_CHECKSUM: "Checksum error",
        NAK_INVALID: "Invalid command",
        NAK_INTERRUPTED: "Movement interrupted by new command",
    }
    return messages.get(code, f"Unknown response code: {code}")

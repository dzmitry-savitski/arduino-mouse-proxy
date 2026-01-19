"""
Arduino Mouse Proxy - Control mouse movements via Arduino Leonardo.
"""

from .client import ArduinoMouse
from .curves import Curve
from .protocol import ProtocolError

__all__ = ["ArduinoMouse", "Curve", "ProtocolError"]
__version__ = "1.0.0"

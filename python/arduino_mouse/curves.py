"""
Easing curve definitions for mouse movement.
"""

from enum import IntEnum


class Curve(IntEnum):
    """
    Easing curves for mouse movement interpolation.

    LINEAR: Constant speed throughout the movement
    EASE_IN: Starts slow, accelerates (quadratic)
    EASE_OUT: Starts fast, decelerates (quadratic)
    EASE_IN_OUT: Smooth acceleration and deceleration (quadratic)
    """
    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2
    EASE_IN_OUT = 3

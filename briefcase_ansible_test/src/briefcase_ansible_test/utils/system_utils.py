"""
System utility functions for cross-platform compatibility.

These utilities provide platform-independent implementations of system functions
that might not be available on all platforms (particularly iOS).
"""

import os


def simple_getuser():
    """
    Cross-platform username getter that doesn't rely on the pwd module.

    This is especially useful on platforms like iOS where the pwd module
    is not available.

    Returns:
        str: The username from environment variables or 'mobile' if not found.
    """
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        user = os.environ.get(name)
        if user:
            return user
    return "mobile"  # Default iOS user

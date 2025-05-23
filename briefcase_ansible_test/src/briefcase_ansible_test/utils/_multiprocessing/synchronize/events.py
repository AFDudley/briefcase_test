"""
Event primitive for iOS multiprocessing compatibility.

This module provides an Event class that mimics multiprocessing.Event
using threading primitives.
"""

import threading


class ThreadEvent:
    """
    Thread-based replacement for multiprocessing.Event.

    Provides the same API as multiprocessing.Event but uses threading.Event internally.
    """

    def __init__(self, *, ctx=None):
        """
        Initialize a new ThreadEvent.

        Args:
            ctx: Context (ignored for compatibility)
        """
        self._event = threading.Event()
        self._ctx = ctx

    def set(self):
        """Set the event."""
        self._event.set()

    def clear(self):
        """Clear the event."""
        self._event.clear()

    def is_set(self):
        """Check if the event is set."""
        return self._event.is_set()

    def wait(self, timeout=None):
        """
        Wait for the event to be set.

        Args:
            timeout: Maximum time to wait

        Returns:
            bool: True if event was set, False if timeout occurred
        """
        return self._event.wait(timeout)
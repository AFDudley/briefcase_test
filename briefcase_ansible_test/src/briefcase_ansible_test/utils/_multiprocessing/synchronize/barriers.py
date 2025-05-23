"""
Barrier primitive for iOS multiprocessing compatibility.

This module provides a Barrier class that mimics multiprocessing.Barrier
using threading primitives.
"""

import threading


class ThreadBarrier:
    """
    Thread-based replacement for multiprocessing.Barrier.

    Provides the same API as multiprocessing.Barrier but uses threading.Barrier internally.
    Note: threading.Barrier is only available in Python 3.2+
    """

    def __init__(self, parties, action=None, timeout=None, *, ctx=None):
        """
        Initialize a new ThreadBarrier.

        Args:
            parties: Number of threads that must wait before barrier is released
            action: Optional callable to run when barrier is released
            timeout: Default timeout for wait operations
            ctx: Context (ignored for compatibility)
        """
        if hasattr(threading, "Barrier"):
            self._barrier = threading.Barrier(parties, action, timeout)
        else:
            # Fallback for older Python versions
            self._barrier = None
            self._parties = parties
            self._action = action
            self._timeout = timeout

        self._ctx = ctx

    def wait(self, timeout=None):
        """
        Wait for the barrier.

        Args:
            timeout: Maximum time to wait

        Returns:
            int: Index of this thread (0 to parties-1)
        """
        if self._barrier is not None:
            return self._barrier.wait(timeout)
        else:
            # Simple fallback - just return 0
            return 0

    def reset(self):
        """Reset the barrier."""
        if self._barrier is not None:
            self._barrier.reset()

    def abort(self):
        """Abort the barrier."""
        if self._barrier is not None:
            self._barrier.abort()

    @property
    def parties(self):
        """Number of parties required."""
        if self._barrier is not None:
            return self._barrier.parties
        else:
            return self._parties

    @property
    def n_waiting(self):
        """Number of threads currently waiting."""
        if self._barrier is not None:
            return self._barrier.n_waiting
        else:
            return 0

    @property
    def broken(self):
        """Whether the barrier is broken."""
        if self._barrier is not None:
            return self._barrier.broken
        else:
            return False
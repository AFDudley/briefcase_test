"""
Lock primitives for iOS multiprocessing compatibility.

This module provides Lock and RLock classes that mimic multiprocessing locks
using threading primitives.
"""

import threading


class ThreadLock:
    """
    Thread-based replacement for multiprocessing.Lock.

    Provides the same API as multiprocessing.Lock but uses threading.Lock internally.
    """

    def __init__(self, *, ctx=None):
        """
        Initialize a new ThreadLock.

        Args:
            ctx: Context (ignored for compatibility)
        """
        self._lock = threading.Lock()
        self._ctx = ctx

    def acquire(self, block=True, timeout=None):
        """
        Acquire the lock.

        Args:
            block: Whether to block waiting for the lock
            timeout: Maximum time to wait for the lock

        Returns:
            bool: True if lock was acquired, False otherwise
        """
        if timeout is None:
            return self._lock.acquire(block)
        else:
            return self._lock.acquire(block, timeout)

    def release(self):
        """Release the lock."""
        self._lock.release()

    def __enter__(self):
        """Context manager entry."""
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._lock.release()
        return False


class ThreadRLock:
    """
    Thread-based replacement for multiprocessing.RLock.

    Provides the same API as multiprocessing.RLock but uses threading.RLock internally.
    """

    def __init__(self, *, ctx=None):
        """
        Initialize a new ThreadRLock.

        Args:
            ctx: Context (ignored for compatibility)
        """
        self._lock = threading.RLock()
        self._ctx = ctx

    def acquire(self, block=True, timeout=None):
        """
        Acquire the lock.

        Args:
            block: Whether to block waiting for the lock
            timeout: Maximum time to wait for the lock

        Returns:
            bool: True if lock was acquired, False otherwise
        """
        if timeout is None:
            return self._lock.acquire(block)
        else:
            return self._lock.acquire(block, timeout)

    def release(self):
        """Release the lock."""
        self._lock.release()

    def __enter__(self):
        """Context manager entry."""
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._lock.release()
        return False

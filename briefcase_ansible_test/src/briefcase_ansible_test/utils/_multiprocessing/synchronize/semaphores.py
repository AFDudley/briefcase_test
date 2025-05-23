"""
Semaphore primitives for iOS multiprocessing compatibility.

This module provides Semaphore and BoundedSemaphore classes that mimic
multiprocessing semaphores using threading primitives.
"""

import threading


class ThreadSemaphore:
    """
    Thread-based replacement for multiprocessing.Semaphore.

    Provides the same API as multiprocessing.Semaphore but uses threading.Semaphore internally.
    """

    def __init__(self, value=1, *, ctx=None):
        """
        Initialize a new ThreadSemaphore.

        Args:
            value: Initial value for the semaphore
            ctx: Context (ignored for compatibility)
        """
        self._semaphore = threading.Semaphore(value)
        self._ctx = ctx

    def acquire(self, block=True, timeout=None):
        """
        Acquire the semaphore.

        Args:
            block: Whether to block waiting for the semaphore
            timeout: Maximum time to wait

        Returns:
            bool: True if semaphore was acquired, False otherwise
        """
        if timeout is None:
            return self._semaphore.acquire(block)
        else:
            return self._semaphore.acquire(block, timeout)

    def release(self):
        """Release the semaphore."""
        self._semaphore.release()

    def __enter__(self):
        """Context manager entry."""
        self._semaphore.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._semaphore.release()
        return False


class ThreadBoundedSemaphore:
    """
    Thread-based replacement for multiprocessing.BoundedSemaphore.

    Provides the same API as multiprocessing.BoundedSemaphore but uses
    threading.BoundedSemaphore internally.
    """

    def __init__(self, value=1, *, ctx=None):
        """
        Initialize a new ThreadBoundedSemaphore.

        Args:
            value: Initial value for the semaphore
            ctx: Context (ignored for compatibility)
        """
        self._semaphore = threading.BoundedSemaphore(value)
        self._ctx = ctx

    def acquire(self, block=True, timeout=None):
        """
        Acquire the semaphore.

        Args:
            block: Whether to block waiting for the semaphore
            timeout: Maximum time to wait

        Returns:
            bool: True if semaphore was acquired, False otherwise
        """
        if timeout is None:
            return self._semaphore.acquire(block)
        else:
            return self._semaphore.acquire(block, timeout)

    def release(self):
        """Release the semaphore."""
        self._semaphore.release()

    def __enter__(self):
        """Context manager entry."""
        self._semaphore.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._semaphore.release()
        return False
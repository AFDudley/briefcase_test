"""
Condition variable primitive for iOS multiprocessing compatibility.

This module provides a Condition class that mimics multiprocessing.Condition
using threading primitives.
"""

import threading


class ThreadCondition:
    """
    Thread-based replacement for multiprocessing.Condition.

    Provides the same API as multiprocessing.Condition but uses threading.Condition internally.
    """

    def __init__(self, lock=None, *, ctx=None):
        """
        Initialize a new ThreadCondition.

        Args:
            lock: Optional lock to use (creates new if None)
            ctx: Context (ignored for compatibility)
        """
        if lock is None:
            lock = threading.RLock()
        elif hasattr(lock, "_lock"):  # Our wrapper classes
            lock = lock._lock

        self._condition = threading.Condition(lock)
        self._ctx = ctx

    def acquire(self, block=True, timeout=None):
        """Acquire the underlying lock."""
        if timeout is None:
            return self._condition.acquire(block)
        else:
            return self._condition.acquire(block, timeout)

    def release(self):
        """Release the underlying lock."""
        self._condition.release()

    def wait(self, timeout=None):
        """
        Wait for notification.

        Args:
            timeout: Maximum time to wait

        Returns:
            bool: True if notified, False if timeout occurred
        """
        return self._condition.wait(timeout)

    def wait_for(self, predicate, timeout=None):
        """
        Wait for a predicate to become true.

        Args:
            predicate: Function that returns True when condition is met
            timeout: Maximum time to wait

        Returns:
            bool: Value of predicate when returning
        """
        return self._condition.wait_for(predicate, timeout)

    def notify(self, n=1):
        """
        Notify n waiting threads.

        Args:
            n: Number of threads to notify
        """
        self._condition.notify(n)

    def notify_all(self):
        """Notify all waiting threads."""
        self._condition.notify_all()

    def __enter__(self):
        """Context manager entry."""
        self._condition.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._condition.release()
        return False

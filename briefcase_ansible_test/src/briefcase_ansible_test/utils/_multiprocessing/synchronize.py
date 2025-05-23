"""
Threading-based synchronization primitives for iOS multiprocessing compatibility.

This module provides synchronization classes that mimic multiprocessing.synchronize
using threading primitives, specifically designed for Ansible compatibility on iOS.
"""

import threading
import time
from typing import Optional, Any


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


# Aliases for compatibility
Lock = ThreadLock
RLock = ThreadRLock
Semaphore = ThreadSemaphore
BoundedSemaphore = ThreadBoundedSemaphore
Event = ThreadEvent
Condition = ThreadCondition
Barrier = ThreadBarrier

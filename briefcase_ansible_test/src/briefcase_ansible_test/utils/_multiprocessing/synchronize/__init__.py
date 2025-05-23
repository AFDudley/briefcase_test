"""
Threading-based synchronization primitives for iOS multiprocessing compatibility.

This package provides synchronization classes that mimic multiprocessing.synchronize
using threading primitives, specifically designed for Ansible compatibility on iOS.
"""

from .locks import ThreadLock, ThreadRLock
from .semaphores import ThreadSemaphore, ThreadBoundedSemaphore
from .events import ThreadEvent
from .conditions import ThreadCondition
from .barriers import ThreadBarrier

# Aliases for compatibility with multiprocessing API
Lock = ThreadLock
RLock = ThreadRLock
Semaphore = ThreadSemaphore
BoundedSemaphore = ThreadBoundedSemaphore
Event = ThreadEvent
Condition = ThreadCondition
Barrier = ThreadBarrier

__all__ = [
    # Thread-prefixed names
    "ThreadLock",
    "ThreadRLock",
    "ThreadSemaphore",
    "ThreadBoundedSemaphore",
    "ThreadEvent",
    "ThreadCondition",
    "ThreadBarrier",
    # Compatibility aliases
    "Lock",
    "RLock",
    "Semaphore",
    "BoundedSemaphore",
    "Event",
    "Condition",
    "Barrier",
]
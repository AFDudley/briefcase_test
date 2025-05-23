"""
Threading-based context management for iOS multiprocessing compatibility.

This module provides context classes that mimic multiprocessing contexts
using threading primitives, specifically designed for Ansible compatibility on iOS.
"""

import sys
import threading
from typing import Type, Any, Optional

from .process import ThreadProcess
from .queues import ProcessQueue, ProcessSimpleQueue, JoinableQueue
from .synchronize import (
    ThreadLock,
    ThreadRLock,
    ThreadSemaphore,
    ThreadBoundedSemaphore,
    ThreadEvent,
    ThreadCondition,
    ThreadBarrier,
)


class ThreadContext:
    """
    Thread-based replacement for multiprocessing context.

    This class provides the same API as multiprocessing contexts but uses
    threading primitives for iOS compatibility. It acts as a factory for
    all multiprocessing-like objects.
    """

    # Process class
    Process = ThreadProcess

    # Queue classes
    Queue = ProcessQueue
    SimpleQueue = ProcessSimpleQueue
    JoinableQueue = JoinableQueue

    # Synchronization classes
    Lock = ThreadLock
    RLock = ThreadRLock
    Semaphore = ThreadSemaphore
    BoundedSemaphore = ThreadBoundedSemaphore
    Event = ThreadEvent
    Condition = ThreadCondition
    Barrier = ThreadBarrier

    def __init__(self, method="thread"):
        """
        Initialize a new ThreadContext.

        Args:
            method: Start method (ignored, always 'thread' for iOS)
        """
        self._method = method

    def get_context(self, method=None):
        """
        Get a context for the specified method.

        Args:
            method: Start method (ignored for iOS)

        Returns:
            ThreadContext: This context instance
        """
        if method is None:
            method = self._method
        return ThreadContext(method)

    def get_start_method(self, allow_none=False):
        """
        Get the current start method.

        Args:
            allow_none: Whether to allow None return

        Returns:
            str: Always 'thread' for iOS
        """
        return "thread"

    def set_start_method(self, method, force=False):
        """
        Set the start method.

        Args:
            method: Start method (ignored for iOS)
            force: Whether to force setting (ignored)
        """
        # For iOS, we always use threading, so this is a no-op
        pass

    def get_all_start_methods(self):
        """
        Get all available start methods.

        Returns:
            list: Always ['thread'] for iOS
        """
        return ["thread"]


class ThreadSpawnContext(ThreadContext):
    """Spawn-style context (same as ThreadContext for iOS)."""

    def __init__(self):
        super().__init__("thread")


class ThreadForkContext(ThreadContext):
    """Fork-style context (same as ThreadContext for iOS since no fork support)."""

    def __init__(self):
        super().__init__("thread")


class ThreadForkServerContext(ThreadContext):
    """Fork server-style context (same as ThreadContext for iOS)."""

    def __init__(self):
        super().__init__("thread")


# Default context for iOS
_default_context = ThreadContext()


def get_context(method=None):
    """
    Get a multiprocessing context.

    Args:
        method: Start method (ignored for iOS)

    Returns:
        ThreadContext: A thread-based context
    """
    if method is None or method == "thread":
        return _default_context
    elif method == "spawn":
        return ThreadSpawnContext()
    elif method == "fork":
        return ThreadForkContext()
    elif method == "forkserver":
        return ThreadForkServerContext()
    else:
        # For any other method, default to thread-based
        return _default_context


def get_start_method(allow_none=False):
    """
    Get the current start method.

    Args:
        allow_none: Whether to allow None return

    Returns:
        str: Always 'thread' for iOS
    """
    return "thread"


def set_start_method(method, force=False):
    """
    Set the start method.

    Args:
        method: Start method (ignored for iOS)
        force: Whether to force setting (ignored)
    """
    # For iOS, we always use threading, so this is a no-op
    pass


def get_all_start_methods():
    """
    Get all available start methods.

    Returns:
        list: Always ['thread'] for iOS
    """
    return ["thread"]


# Aliases for global access
Process = _default_context.Process
Queue = _default_context.Queue
SimpleQueue = _default_context.SimpleQueue
JoinableQueue = _default_context.JoinableQueue
Lock = _default_context.Lock
RLock = _default_context.RLock
Semaphore = _default_context.Semaphore
BoundedSemaphore = _default_context.BoundedSemaphore
Event = _default_context.Event
Condition = _default_context.Condition
Barrier = _default_context.Barrier

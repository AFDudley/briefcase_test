"""
Threading-based Queue implementations for iOS multiprocessing compatibility.

This module provides Queue classes that mimic multiprocessing queues using
threading primitives, specifically designed for Ansible compatibility on iOS.
"""

import queue
import threading
import time
import pickle
import sys
import traceback
from typing import Any, Optional, Union


class BaseQueue:
    """Base queue class to support proper inheritance."""

    pass


class ProcessQueue(BaseQueue):
    """
    Thread-based replacement for multiprocessing.Queue.

    This class provides the same API as multiprocessing.Queue but uses threading
    queue internally for iOS compatibility. It includes exception serialization
    and process-like behavior for Ansible compatibility.
    """

    def __init__(self, maxsize=0, *, ctx=None):
        """
        Initialize a new ProcessQueue.

        Args:
            maxsize: Maximum size of the queue (0 = unlimited)
            ctx: Context (ignored for compatibility)
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._ctx = ctx
        self._closed = False
        self._lock = threading.RLock()

    def put(self, item, block=True, timeout=None):
        """
        Put an item into the queue.

        Args:
            item: The item to put
            block: Whether to block if queue is full
            timeout: Maximum time to wait

        Raises:
            queue.Full: If queue is full and block=False or timeout expired
        """
        if self._closed:
            raise ValueError("Queue is closed")

        # Serialize exceptions for cross-"process" compatibility
        if isinstance(item, Exception):
            item = self._serialize_exception(item)

        self._queue.put(item, block=block, timeout=timeout)

    def get(self, block=True, timeout=None):
        """
        Get an item from the queue.

        Args:
            block: Whether to block if queue is empty
            timeout: Maximum time to wait

        Returns:
            The item from the queue

        Raises:
            queue.Empty: If queue is empty and block=False or timeout expired
            Exception: Any exception that was put into the queue
        """
        if self._closed:
            raise ValueError("Queue is closed")

        item = self._queue.get(block=block, timeout=timeout)

        # Deserialize exceptions
        if isinstance(item, dict) and item.get("__exception__"):
            return self._deserialize_exception(item)

        return item

    def put_nowait(self, item):
        """Put an item without blocking."""
        return self.put(item, block=False)

    def get_nowait(self):
        """Get an item without blocking."""
        return self.get(block=False)

    def empty(self):
        """Check if the queue is empty."""
        return self._queue.empty()

    def full(self):
        """Check if the queue is full."""
        return self._queue.full()

    def qsize(self):
        """Get the approximate size of the queue."""
        return self._queue.qsize()

    def close(self):
        """Close the queue."""
        with self._lock:
            self._closed = True

    def join_thread(self):
        """Join the background thread (no-op for compatibility)."""
        pass

    def cancel_join_thread(self):
        """Cancel joining the background thread (no-op for compatibility)."""
        pass

    def _serialize_exception(self, exc):
        """
        Serialize an exception for queue transport.

        Args:
            exc: The exception to serialize

        Returns:
            dict: Serialized exception data
        """
        try:
            return {
                "__exception__": True,
                "type": exc.__class__.__module__ + "." + exc.__class__.__name__,
                "args": exc.args,
                "traceback": traceback.format_exc(),
                "pickled": pickle.dumps(exc),
            }
        except Exception:
            # Fallback if pickling fails
            return {
                "__exception__": True,
                "type": "Exception",
                "args": (str(exc),),
                "traceback": traceback.format_exc(),
                "pickled": None,
            }

    def _deserialize_exception(self, data):
        """
        Deserialize an exception from queue data.

        Args:
            data: Serialized exception data

        Returns:
            Exception: The deserialized exception
        """
        try:
            if data.get("pickled"):
                return pickle.loads(data["pickled"])
        except Exception:
            pass

        # Fallback to generic exception
        exc_type = data.get("type", "Exception")
        args = data.get("args", ())

        try:
            # Try to reconstruct the original exception type
            if "." in exc_type:
                module_name, class_name = exc_type.rsplit(".", 1)
                module = sys.modules.get(module_name)
                if module and hasattr(module, class_name):
                    exc_class = getattr(module, class_name)
                    return exc_class(*args)
        except Exception:
            pass

        # Final fallback
        return Exception(*args)


class ProcessSimpleQueue:
    """
    Thread-based replacement for multiprocessing.SimpleQueue.

    This class provides the same API as multiprocessing.SimpleQueue but uses
    threading queue internally for iOS compatibility.
    """

    def __init__(self, *, ctx=None):
        """
        Initialize a new ProcessSimpleQueue.

        Args:
            ctx: Context (ignored for compatibility)
        """
        self._queue = queue.SimpleQueue()
        self._ctx = ctx
        self._closed = False

    def put(self, item):
        """
        Put an item into the queue.

        Args:
            item: The item to put
        """
        if self._closed:
            raise ValueError("Queue is closed")

        # Serialize exceptions for cross-"process" compatibility
        if isinstance(item, Exception):
            item = self._serialize_exception(item)

        self._queue.put(item)

    def get(self, block=True, timeout=None):
        """
        Get an item from the queue.

        Args:
            block: Whether to block if queue is empty
            timeout: Timeout in seconds for blocking get

        Returns:
            The item from the queue

        Raises:
            Exception: Any exception that was put into the queue
            Empty: If timeout occurs and no item available
        """
        if self._closed:
            raise ValueError("Queue is closed")

        try:
            item = self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            raise

        # Deserialize exceptions
        if isinstance(item, dict) and item.get("__exception__"):
            exc = self._deserialize_exception(item)
            raise exc

        return item

    def empty(self):
        """Check if the queue is empty."""
        return self._queue.empty()

    def qsize(self):
        """Get the approximate size of the queue."""
        return self._queue.qsize()

    def close(self):
        """Close the queue."""
        self._closed = True

    def _serialize_exception(self, exc):
        """Serialize an exception (same as ProcessQueue)."""
        try:
            return {
                "__exception__": True,
                "type": exc.__class__.__module__ + "." + exc.__class__.__name__,
                "args": exc.args,
                "traceback": traceback.format_exc(),
                "pickled": pickle.dumps(exc),
            }
        except Exception:
            return {
                "__exception__": True,
                "type": "Exception",
                "args": (str(exc),),
                "traceback": traceback.format_exc(),
                "pickled": None,
            }

    def _deserialize_exception(self, data):
        """Deserialize an exception (same as ProcessQueue)."""
        try:
            if data.get("pickled"):
                return pickle.loads(data["pickled"])
        except Exception:
            pass

        exc_type = data.get("type", "Exception")
        args = data.get("args", ())

        try:
            if "." in exc_type:
                module_name, class_name = exc_type.rsplit(".", 1)
                module = sys.modules.get(module_name)
                if module and hasattr(module, class_name):
                    exc_class = getattr(module, class_name)
                    return exc_class(*args)
        except Exception:
            pass

        return Exception(*args)


class JoinableQueue(ProcessQueue):
    """
    Thread-based replacement for multiprocessing.JoinableQueue.

    This extends ProcessQueue with task tracking for join() functionality.
    """

    def __init__(self, maxsize=0, *, ctx=None):
        """Initialize a new JoinableQueue."""
        super().__init__(maxsize, ctx=ctx)
        self._unfinished_tasks = 0
        self._finished = threading.Condition(self._lock)

    def put(self, item, block=True, timeout=None):
        """Put an item and increment unfinished task count."""
        super().put(item, block, timeout)
        with self._finished:
            self._unfinished_tasks += 1

    def task_done(self):
        """Mark a task as done."""
        with self._finished:
            if self._unfinished_tasks <= 0:
                raise ValueError("task_done() called too many times")
            self._unfinished_tasks -= 1
            if self._unfinished_tasks == 0:
                self._finished.notify_all()

    def join(self):
        """Wait until all tasks are done."""
        with self._finished:
            while self._unfinished_tasks:
                self._finished.wait()


# Aliases for compatibility
Queue = ProcessQueue
SimpleQueue = ProcessSimpleQueue

# Export base class for inheritance support
__all__ = [
    "ProcessQueue",
    "ProcessSimpleQueue",
    "JoinableQueue",
    "Queue",
    "SimpleQueue",
    "BaseQueue",
]

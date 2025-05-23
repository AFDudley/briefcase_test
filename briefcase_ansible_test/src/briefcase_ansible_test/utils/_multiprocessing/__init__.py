"""
iOS-compatible multiprocessing module using threading primitives.

This module provides a drop-in replacement for Python's multiprocessing module
on platforms where multiprocessing is not available (like iOS). It implements
the multiprocessing API using threading primitives while maintaining API
compatibility for applications like Ansible.

Key Features:
- Full Process API compatibility using ThreadProcess
- Queue implementations with exception serialization
- Synchronization primitives (Lock, RLock, Semaphore, etc.)
- Context management for different "start methods"
- Exception propagation across "processes"

Usage:
    import briefcase_ansible_test.utils._multiprocessing as multiprocessing

    # Use exactly like regular multiprocessing
    p = multiprocessing.Process(target=my_function, args=(arg1, arg2))
    p.start()
    p.join()

See multiprocessing_ios_analysis.md for detailed architecture and implementation notes.
"""

import sys
import os

# Import all components
from .context import (
    ThreadContext,
    get_context,
    get_start_method,
    set_start_method,
    get_all_start_methods,
)
from .process import ThreadProcess, BaseProcess
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

# Default context for global access
_default_context = get_context()

# Export main classes and functions
Process = ThreadProcess
Queue = ProcessQueue
SimpleQueue = ProcessSimpleQueue
JoinableQueue = JoinableQueue

# Synchronization primitives
Lock = ThreadLock
RLock = ThreadRLock
Semaphore = ThreadSemaphore
BoundedSemaphore = ThreadBoundedSemaphore
Event = ThreadEvent
Condition = ThreadCondition
Barrier = ThreadBarrier

# Context management
current_process = lambda: _FakeProcess()
active_children = lambda: []
cpu_count = lambda: 1  # iOS typically single-core for Python


class _FakeProcess:
    """
    Fake process object for current_process() compatibility.
    """

    def __init__(self):
        self.name = "MainThread"
        self.pid = os.getpid() if hasattr(os, "getpid") else 1
        self.daemon = False

    def is_alive(self):
        return True


# Pool implementation for basic compatibility
class ThreadPool:
    """
    Basic thread pool implementation for multiprocessing.Pool compatibility.

    This is a simplified version that provides the essential Pool API
    methods needed by Ansible, using ThreadPoolExecutor internally.
    """

    def __init__(
        self, processes=None, initializer=None, initargs=(), maxtasksperchild=None
    ):
        """
        Initialize the thread pool.

        Args:
            processes: Number of worker threads (defaults to 1 for iOS)
            initializer: Function to run on worker startup
            initargs: Arguments for initializer
            maxtasksperchild: Max tasks per worker (ignored)
        """
        import concurrent.futures

        if processes is None:
            processes = 1  # Conservative for iOS

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=processes)
        self._closed = False

        # Run initializer if provided
        if initializer:
            for _ in range(processes):
                self._executor.submit(initializer, *initargs)

    def apply(self, func, args=(), kwds=None):
        """Apply function with arguments."""
        if kwds is None:
            kwds = {}
        if self._closed:
            raise ValueError("Pool is closed")

        future = self._executor.submit(func, *args, **kwds)
        return future.result()

    def apply_async(self, func, args=(), kwds=None, callback=None, error_callback=None):
        """Apply function asynchronously."""
        if kwds is None:
            kwds = {}
        if self._closed:
            raise ValueError("Pool is closed")

        future = self._executor.submit(func, *args, **kwds)

        # Handle callbacks
        if callback or error_callback:

            def handle_result(fut):
                try:
                    result = fut.result()
                    if callback:
                        callback(result)
                except Exception as e:
                    if error_callback:
                        error_callback(e)

            future.add_done_callback(handle_result)

        return _AsyncResult(future)

    def map(self, func, iterable, chunksize=None):
        """Map function over iterable."""
        if self._closed:
            raise ValueError("Pool is closed")

        results = list(self._executor.map(func, iterable))
        return results

    def imap(self, func, iterable, chunksize=None):
        """Map function over iterable, returning iterator."""
        if self._closed:
            raise ValueError("Pool is closed")

        return self._executor.map(func, iterable)

    def close(self):
        """Close the pool to new tasks."""
        self._closed = True

    def terminate(self):
        """Terminate the pool."""
        self._closed = True
        self._executor.shutdown(wait=False)

    def join(self):
        """Wait for all tasks to complete."""
        self._executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
        self.join()


class _AsyncResult:
    """
    Wrapper for concurrent.futures.Future to mimic multiprocessing.AsyncResult.
    """

    def __init__(self, future):
        self._future = future

    def get(self, timeout=None):
        """Get the result."""
        return self._future.result(timeout)

    def wait(self, timeout=None):
        """Wait for completion."""
        import concurrent.futures

        done, _ = concurrent.futures.wait([self._future], timeout=timeout)
        return len(done) > 0

    def ready(self):
        """Check if result is ready."""
        return self._future.done()

    def successful(self):
        """Check if completed successfully."""
        return self._future.done() and self._future.exception() is None


# Pool alias
Pool = ThreadPool

# Version info for compatibility
__version__ = "1.0.0-ios-threading"

# All exports
__all__ = [
    # Process and execution
    "Process",
    "current_process",
    "active_children",
    # Queues
    "Queue",
    "SimpleQueue",
    "JoinableQueue",
    # Synchronization
    "Lock",
    "RLock",
    "Semaphore",
    "BoundedSemaphore",
    "Event",
    "Condition",
    "Barrier",
    # Context management
    "get_context",
    "get_start_method",
    "set_start_method",
    "get_all_start_methods",
    # Pool
    "Pool",
    "pool",
    # Utility
    "cpu_count",
]

# Create pool submodule for import compatibility
pool = type(
    "pool_module",
    (),
    {
        "Pool": Pool,
        "ThreadPool": ThreadPool,
    },
)()


def _patch_system_modules():
    """
    Patch system modules to use our threading-based multiprocessing.

    This ensures that when other modules import multiprocessing, they get
    our iOS-compatible version instead of the system version.
    """
    # Replace multiprocessing in sys.modules
    sys.modules["multiprocessing"] = sys.modules[__name__]  # type: ignore

    # Create minimal submodules to avoid import conflicts
    # We need to be careful not to create circular references or complex objects
    # that might cause issues during Ansible's import process

    # Process module - minimal exports
    process_module = type("Module", (), {})()
    process_module.Process = Process  # type: ignore
    process_module.BaseProcess = BaseProcess  # type: ignore
    process_module.current_process = current_process  # type: ignore
    process_module.active_children = active_children  # type: ignore
    sys.modules["multiprocessing.process"] = process_module  # type: ignore

    # Queues module - minimal exports
    queues_module = type("Module", (), {})()
    queues_module.Queue = Queue  # type: ignore
    queues_module.SimpleQueue = SimpleQueue  # type: ignore
    queues_module.JoinableQueue = JoinableQueue  # type: ignore
    sys.modules["multiprocessing.queues"] = queues_module  # type: ignore

    # Synchronize module - minimal exports
    sync_module = type("Module", (), {})()
    sync_module.Lock = Lock  # type: ignore
    sync_module.RLock = RLock  # type: ignore
    sync_module.Semaphore = Semaphore  # type: ignore
    sync_module.BoundedSemaphore = BoundedSemaphore  # type: ignore
    sync_module.Event = Event  # type: ignore
    sync_module.Condition = Condition  # type: ignore
    sync_module.Barrier = Barrier  # type: ignore
    sys.modules["multiprocessing.synchronize"] = sync_module  # type: ignore

    # Context module - minimal exports
    context_module = type("Module", (), {})()
    context_module.Process = Process  # type: ignore
    context_module.get_context = get_context  # type: ignore
    context_module.get_start_method = get_start_method  # type: ignore
    context_module.set_start_method = set_start_method  # type: ignore
    sys.modules["multiprocessing.context"] = context_module  # type: ignore

    # Pool module
    sys.modules["multiprocessing.pool"] = pool  # type: ignore


# Auto-patch on import
_patch_system_modules()

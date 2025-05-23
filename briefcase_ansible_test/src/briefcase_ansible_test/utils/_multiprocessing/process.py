"""
Threading-based Process implementation for iOS multiprocessing compatibility.

This module provides a Process class that mimics multiprocessing.Process using
threading primitives, specifically designed for Ansible compatibility on iOS.
"""

import threading
import queue
import time
import sys
import traceback
import os
import signal
from typing import Optional, Callable, Any, Tuple


class BaseProcess:
    """
    Base class that mimics multiprocessing.process.BaseProcess.

    This provides the base interface that multiprocessing.Process inherits from.
    """

    pass


class ThreadProcess(BaseProcess):
    """
    Thread-based replacement for multiprocessing.Process.

    This class provides the same API as multiprocessing.Process but uses threading
    internally to ensure iOS compatibility. It maintains state tracking, exception
    propagation, and proper lifecycle management.
    """

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None
    ):
        """
        Initialize a new ThreadProcess.

        Args:
            group: Ignored for compatibility (multiprocessing groups not supported)
            target: The callable to execute in the thread
            name: Optional name for the process/thread
            args: Arguments to pass to target
            kwargs: Keyword arguments to pass to target
            daemon: Whether this should be a daemon thread
        """
        if kwargs is None:
            kwargs = {}

        self._group = group
        self._target = target
        self._name = name or f"ThreadProcess-{id(self)}"
        self._args = args
        self._kwargs = kwargs
        self._daemon = daemon

        # Thread and state management
        self._thread: Optional[threading.Thread] = None
        self._started = False
        self._exitcode: Optional[int] = None
        self._pid = None

        # Exception and result handling
        self._exception_queue = queue.SimpleQueue()
        self._result_queue = queue.SimpleQueue()
        self._exception_info: Optional[Tuple[type, Exception, str]] = None

        # Termination support
        self._terminate_event = threading.Event()

    @property
    def name(self) -> str:
        """Get the process name."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the process name."""
        self._name = value
        if self._thread:
            self._thread.name = value

    @property
    def daemon(self) -> Optional[bool]:
        """Get daemon status."""
        return self._daemon

    @daemon.setter
    def daemon(self, value: bool):
        """Set daemon status."""
        if self._started:
            raise RuntimeError("cannot set daemon status of active process")
        self._daemon = value

    @property
    def pid(self) -> Optional[int]:
        """Get process ID (simulated)."""
        return self._pid

    @property
    def exitcode(self) -> Optional[int]:
        """
        Get the exit code.

        Returns:
            None if not started or still running
            0 if completed successfully
            Negative value if terminated by signal
            Positive value if exited with error
        """
        if not self._started:
            return None
        if self.is_alive():
            return None
        return self._exitcode

    def is_alive(self) -> bool:
        """Check if the process is currently running."""
        if not self._started or self._thread is None:
            return False
        return self._thread.is_alive()

    def start(self):
        """Start the process execution."""
        if self._started:
            raise RuntimeError("process has already started")

        self._started = True
        self._pid = threading.get_ident()  # Use thread ID as PID

        # Create and configure the thread
        self._thread = threading.Thread(
            target=self._run_wrapper, name=self._name, daemon=self._daemon
        )

        self._thread.start()

    def join(self, timeout=None):
        """
        Wait for the process to complete.

        Args:
            timeout: Maximum time to wait in seconds
        """
        if not self._started:
            raise RuntimeError("can only join a started process")

        if self._thread is None:
            return

        self._thread.join(timeout)

        # After joining, check for exceptions
        self._check_for_exceptions()

    def terminate(self):
        """Request termination of the process."""
        if not self.is_alive():
            return

        self._terminate_event.set()
        # Give the thread a moment to clean up
        time.sleep(0.01)

    def kill(self):
        """Forcefully terminate the process (same as terminate for threads)."""
        self.terminate()

    def run(self):
        """
        Method to be overridden by subclasses.

        This is the default run method that gets called when no target function
        is provided. Subclasses (like Ansible's WorkerProcess) override this
        method to define their behavior.
        """
        # Default implementation does nothing, like multiprocessing.Process
        pass

    def close(self):
        """Clean up resources."""
        if self.is_alive():
            self.terminate()
            self.join(timeout=1.0)

    def __del__(self):
        """Destructor to clean up resources."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup

    def _run_wrapper(self):
        """
        Internal wrapper that executes the target function and handles exceptions.
        """
        try:
            # Check for termination request before starting
            if self._terminate_event.is_set():
                self._exitcode = -signal.SIGTERM
                return

            # Execute the target function or overridden run method
            if self._target is not None:
                # Standard usage: Process(target=function, args=...)
                result = self._target(*self._args, **self._kwargs)
            else:
                # Subclass usage: class MyProcess(Process): def run(self): ...
                # This is how Ansible's WorkerProcess works
                result = self.run()

            # Store result if successful
            self._result_queue.put(result)
            self._exitcode = 0

        except Exception as e:
            # Capture exception with full traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_str = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )

            if exc_type is not None and exc_value is not None:
                self._exception_info = (exc_type, exc_value, tb_str)  # type: ignore
                self._exception_queue.put(self._exception_info)
            self._exitcode = 1

        except BaseException as e:
            # Handle system exit and other base exceptions
            self._exitcode = getattr(e, "code", 1)

    def _check_for_exceptions(self):
        """Check if any exceptions occurred and re-raise them."""
        try:
            while True:
                exc_info = self._exception_queue.get_nowait()
                if exc_info:
                    exc_type, exc_value, tb_str = exc_info
                    # Store for later access
                    self._exception_info = exc_info
                    # For now, we don't re-raise as multiprocessing doesn't by default
                    break
        except queue.Empty:
            pass

    def get_result(self):
        """
        Get the result of the target function execution.

        Returns:
            The return value of the target function

        Raises:
            RuntimeError: If the process hasn't completed successfully
            Exception: Any exception that occurred in the target function
        """
        if self.is_alive():
            raise RuntimeError("Process is still running")

        if self._exception_info:
            exc_type, exc_value, tb_str = self._exception_info
            raise exc_value

        try:
            return self._result_queue.get_nowait()
        except queue.Empty:
            return None

    def __repr__(self):
        """String representation of the process."""
        status = "initial"
        if self._started:
            if self.is_alive():
                status = "started"
            else:
                status = f"stopped[{self._exitcode}]"

        return f"<{self.__class__.__name__}({self._name}, {status})>"


# Alias for compatibility
Process = ThreadProcess

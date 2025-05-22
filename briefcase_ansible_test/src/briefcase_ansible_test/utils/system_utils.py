"""
System utility functions for cross-platform compatibility.

These utilities provide platform-independent implementations of system functions
that might not be available on all platforms (particularly iOS).
"""

import os
import sys
import getpass
import threading
import types


def simple_getuser():
    """
    Cross-platform username getter that doesn't rely on the pwd module.

    This is especially useful on platforms like iOS where the pwd module
    is not available.

    Returns:
        str: The username from environment variables or 'mobile' if not found.
    """
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        user = os.environ.get(name)
        if user:
            return user
    return "mobile"  # Default iOS user


class PwdModule:
    """
    A mock implementation of the pwd module for platforms where it's not available.

    This provides the minimum functionality needed by Ansible and other libraries
    that expect the pwd module to be present.
    """

    class Struct:
        """
        A simple structure class that can be used to create objects with arbitrary attributes.
        """

        def __init__(self, **entries):
            """
            Initialize the structure with the given key-value pairs as attributes.

            Args:
                **entries: Arbitrary keyword arguments that will become attributes.
            """
            self.__dict__.update(entries)

    def getpwuid(self, uid):
        """
        Get a passwd struct by user ID.

        Args:
            uid: The user ID (ignored in this implementation).

        Returns:
            Struct: A struct with a pw_name attribute set to 'mobile'.
        """
        return self.Struct(pw_name="mobile")

    def getpwnam(self, name):
        """
        Get a passwd struct by username.

        Args:
            name: The username (ignored in this implementation).

        Returns:
            Struct: A struct with pw_uid, pw_gid, and pw_dir attributes.
        """
        return self.Struct(pw_uid=0, pw_gid=0, pw_dir="/home/mobile")


def setup_pwd_module_mock():
    """
    Install a mock pwd module in sys.modules if it doesn't already exist.

    This should be called before importing any modules that might depend on
    the pwd module, particularly on platforms where pwd is not available.
    """
    if "pwd" not in sys.modules:
        import types

        class PwdModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("pwd")
                self.getpwuid = PwdModule().getpwuid
                self.getpwnam = PwdModule().getpwnam

        sys.modules["pwd"] = PwdModuleType()


def patch_getpass():
    """
    Replace getpass.getuser with our simple_getuser implementation.

    This should be called before any code that might use getpass.getuser.
    """
    getpass.getuser = simple_getuser


class GrpModule:
    """
    A mock implementation of the grp module for platforms where it's not available.

    This provides the minimum functionality needed by Ansible and other libraries
    that expect the grp module to be present.
    """

    class Struct:
        """
        A simple structure class that can be used to create objects with arbitrary attributes.
        """

        def __init__(self, **entries):
            """
            Initialize the structure with the given key-value pairs as attributes.
            """
            self.__dict__.update(entries)

    def getgrgid(self, gid):
        """
        Get a group struct by group ID.

        Args:
            gid: The group ID (ignored in this implementation).

        Returns:
            Struct: A struct with a gr_name attribute set to 'mobile'.
        """
        return self.Struct(gr_name="mobile")

    def getgrnam(self, name):
        """
        Get a group struct by group name.

        Args:
            name: The group name (ignored in this implementation).

        Returns:
            Struct: A struct with gr_gid attribute and empty gr_mem list.
        """
        return self.Struct(gr_gid=0, gr_mem=[])


def setup_grp_module_mock():
    """
    Install a mock grp module in sys.modules if it doesn't already exist.

    This should be called before importing any modules that might depend on
    the grp module, particularly on platforms where grp is not available.
    """
    if "grp" not in sys.modules:
        import types

        class GrpModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("grp")
                self.getgrgid = GrpModule().getgrgid
                self.getgrnam = GrpModule().getgrnam

        sys.modules["grp"] = GrpModuleType()


def setup_multiprocessing_mock():
    """
    Install comprehensive mocks for multiprocessing modules in sys.modules.
    
    This prevents errors when code tries to use multiprocessing features
    that aren't available on iOS, including the sem_open issue (Python issue 3770).
    """
    # Create wrapper classes that accept keyword arguments but ignore them
    class LockWrapper:
        def __init__(self, *args, **kwargs):
            self._lock = threading.Lock()
        def __call__(self, *args, **kwargs):
            return self._lock
        def acquire(self, *args, **kwargs):
            return self._lock.acquire()
        def release(self):
            return self._lock.release()
        def __enter__(self):
            return self._lock.__enter__()
        def __exit__(self, *args):
            return self._lock.__exit__(*args)
    
    class RLockWrapper:
        def __init__(self, *args, **kwargs):
            self._lock = threading.RLock()
        def __call__(self, *args, **kwargs):
            return self._lock
        def acquire(self, *args, **kwargs):
            return self._lock.acquire()
        def release(self):
            return self._lock.release()
        def __enter__(self):
            return self._lock.__enter__()
        def __exit__(self, *args):
            return self._lock.__exit__(*args)
    
    # Mock the _multiprocessing module with all required components
    if "_multiprocessing" not in sys.modules:
        class MultiprocessingModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("_multiprocessing")
                # Mock SemLock with our wrapper
                self.SemLock = LockWrapper
                # Mock sem_unlink function
                self.sem_unlink = lambda name: None
                # Mock Connection
                self.Connection = object
        
        sys.modules["_multiprocessing"] = MultiprocessingModuleType()
    
    # Mock the multiprocessing.synchronize module to avoid sem_open issues
    if "multiprocessing.synchronize" not in sys.modules:
        class SynchronizeModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("multiprocessing.synchronize")
                # Use our wrapper classes that accept keyword arguments
                self.Lock = LockWrapper
                self.RLock = RLockWrapper
                self.Semaphore = lambda *args, **kwargs: threading.Semaphore()
                self.BoundedSemaphore = lambda *args, **kwargs: threading.BoundedSemaphore()
                self.Event = lambda *args, **kwargs: threading.Event()
                self.Condition = lambda *args, **kwargs: threading.Condition()
                # Mock Barrier (not available in all Python versions)
                if hasattr(threading, 'Barrier'):
                    self.Barrier = lambda parties, *args, **kwargs: threading.Barrier(parties)
                else:
                    self.Barrier = lambda *args, **kwargs: None
        
        sys.modules["multiprocessing.synchronize"] = SynchronizeModuleType()
    
    # Mock multiprocessing.queues module
    if "multiprocessing.queues" not in sys.modules:
        import queue
        
        class SimpleQueueMock:
            """Mock for multiprocessing.queues.SimpleQueue using threading queue"""
            def __init__(self, *args, **kwargs):
                self._queue = queue.SimpleQueue()
            
            def put(self, item):
                return self._queue.put(item)
            
            def get(self, block=True, timeout=None):
                return self._queue.get(block=block, timeout=timeout)
            
            def empty(self):
                return self._queue.empty()
            
            def qsize(self):
                return self._queue.qsize()
        
        class QueuesModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("multiprocessing.queues")
                self.SimpleQueue = SimpleQueueMock
                self.Queue = SimpleQueueMock  # Fallback to same implementation
        
        sys.modules["multiprocessing.queues"] = QueuesModuleType()
    
    # Mock the main multiprocessing module to provide access to submodules
    if "multiprocessing" not in sys.modules:
        class MainMultiprocessingModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("multiprocessing")
                # Add other common multiprocessing attributes
                self.Lock = LockWrapper
                self.RLock = RLockWrapper
                self.Queue = SimpleQueueMock
                self.Process = threading.Thread  # Use Thread as Process mock
            
            @property
            def queues(self):
                # Lazily access queues submodule to avoid initialization order issues
                return sys.modules.get("multiprocessing.queues")
            
            @property
            def synchronize(self):
                # Lazily access synchronize submodule
                return sys.modules.get("multiprocessing.synchronize")
        
        sys.modules["multiprocessing"] = MainMultiprocessingModuleType()

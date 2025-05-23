#!/usr/bin/env python3
"""
Debug script to trace exactly where Ansible task execution hangs.

This script instruments key components to identify the exact location
where execution blocks during task execution.
"""

import sys
import threading
import time
import signal
import functools

sys.path.insert(0, "src")

# Patch multiprocessing first
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

# Apply system patches
from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()


class ExecutionTracer:
    """Tracer to monitor execution flow and identify hanging points."""

    def __init__(self):
        self.steps = []
        self.lock = threading.Lock()

    def log(self, message):
        """Log an execution step with timestamp."""
        with self.lock:
            timestamp = time.time()
            thread_name = threading.current_thread().name
            self.steps.append((timestamp, thread_name, message))
            print(f"[{timestamp:.3f}] [{thread_name}] {message}")

    def dump_trace(self):
        """Dump all execution steps for analysis."""
        print("\n" + "=" * 50)
        print("EXECUTION TRACE:")
        print("=" * 50)
        for timestamp, thread_name, message in self.steps:
            print(f"[{timestamp:.3f}] [{thread_name}] {message}")
        print("=" * 50)


tracer = ExecutionTracer()


def trace_method(cls, method_name):
    """Decorator to trace method calls on a class."""
    original_method = getattr(cls, method_name)

    @functools.wraps(original_method)
    def traced_method(self, *args, **kwargs):
        tracer.log(f"{cls.__name__}.{method_name}() called")
        try:
            result = original_method(self, *args, **kwargs)
            tracer.log(f"{cls.__name__}.{method_name}() completed")
            return result
        except Exception as e:
            tracer.log(f"{cls.__name__}.{method_name}() failed with {e}")
            raise

    setattr(cls, method_name, traced_method)


def timeout_handler(signum, frame):
    """Handle timeout by dumping trace and exiting."""
    print("\n🚨 TIMEOUT REACHED!")
    tracer.dump_trace()
    print("\n💡 ANALYSIS:")
    print("The last logged step shows where execution hung.")
    print("Look for methods that were called but never completed.")
    sys.exit(1)


# Set a timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(20)  # 20 second timeout

try:
    tracer.log("Starting instrumented Ansible test")

    # Import and instrument key classes
    tracer.log("Importing Ansible components")
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.executor.task_executor import TaskExecutor
    from ansible.executor.process.worker import WorkerProcess
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    tracer.log("Ansible imports completed")

    # Instrument key classes to trace their execution
    tracer.log("Instrumenting key classes")

    # Instrument TaskQueueManager
    trace_method(TaskQueueManager, "run")
    # Only instrument methods that exist
    if hasattr(TaskQueueManager, "_initialize_processes"):
        trace_method(TaskQueueManager, "_initialize_processes")

    # Instrument WorkerProcess (our ThreadProcess subclass)
    trace_method(WorkerProcess, "__init__")
    trace_method(WorkerProcess, "start")
    trace_method(WorkerProcess, "join")
    trace_method(WorkerProcess, "run")

    # Instrument TaskExecutor
    trace_method(TaskExecutor, "run")

    # Instrument our ThreadProcess directly
    from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess

    trace_method(ThreadProcess, "__init__")
    trace_method(ThreadProcess, "start")
    trace_method(ThreadProcess, "join")
    trace_method(ThreadProcess, "_run_wrapper")

    tracer.log("Instrumentation completed")

    # Initialize plugin loader
    tracer.log("Initializing plugin loader")
    init_plugin_loader()

    # Set up minimal context
    tracer.log("Setting up Ansible context")
    context.CLIARGS = ImmutableDict(
        {
            "connection": "local",
            "forks": 1,
            "become": None,
            "become_method": None,
            "become_user": None,
            "check": False,
            "diff": False,
            "verbosity": 0,
        }
    )

    # Create minimal components
    tracer.log("Creating Ansible components")
    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=["localhost,"])
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Define simple play
    tracer.log("Creating Ansible play")
    play_source = {
        "name": "Debug Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {
                "name": "Simple debug task",
                "debug": {"msg": "Testing iOS multiprocessing"},
            }
        ],
    }

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # Create TaskQueueManager
    tracer.log("Creating TaskQueueManager")
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )

    tracer.log("TaskQueueManager created, starting execution")

    # This is where the hang occurs
    tracer.log("Calling tqm.run(play) - CRITICAL POINT")
    result = tqm.run(play)

    tracer.log(f"tqm.run(play) completed with result: {result}")

    # Cleanup
    tracer.log("Starting cleanup")
    tqm.cleanup()
    tracer.log("Cleanup completed")

    signal.alarm(0)  # Cancel timeout
    tracer.log("🎉 SUCCESS: Test completed without hanging!")

except Exception as e:
    signal.alarm(0)  # Cancel timeout
    tracer.log(f"❌ EXCEPTION: {e}")
    import traceback

    traceback.print_exc()
    tracer.dump_trace()
    sys.exit(1)

finally:
    tracer.dump_trace()

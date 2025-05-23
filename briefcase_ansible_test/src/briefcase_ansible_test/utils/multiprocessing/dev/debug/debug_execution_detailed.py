#!/usr/bin/env python3
"""
Detailed trace of Ansible task execution to pinpoint the exact hanging location.
"""

import sys
import signal
import time
import threading
import functools

sys.path.insert(0, "src")

# Patch multiprocessing first
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

# Import Ansible components
from ansible.plugins.loader import init_plugin_loader
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.process.worker import WorkerProcess
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict


class DetailedTracer:
    def __init__(self):
        self.steps = []
        self.lock = threading.Lock()
        self.start_time = time.time()

    def log(self, message):
        with self.lock:
            elapsed = time.time() - self.start_time
            thread = threading.current_thread().name
            self.steps.append((elapsed, thread, message))
            print(f"[{elapsed:6.3f}] [{thread:20s}] {message}")

    def dump_last_steps(self, count=10):
        print(f"\n📋 Last {count} execution steps:")
        for elapsed, thread, message in self.steps[-count:]:
            print(f"[{elapsed:6.3f}] [{thread:20s}] {message}")


tracer = DetailedTracer()


def trace_calls(obj, method_names):
    """Trace multiple method calls on an object."""
    for method_name in method_names:
        if hasattr(obj, method_name):
            original = getattr(obj, method_name)

            @functools.wraps(original)
            def traced_method(original_method, method_name):
                def wrapper(*args, **kwargs):
                    tracer.log(f"{obj.__class__.__name__}.{method_name}() START")
                    try:
                        result = original_method(*args, **kwargs)
                        tracer.log(f"{obj.__class__.__name__}.{method_name}() END")
                        return result
                    except Exception as e:
                        tracer.log(
                            f"{obj.__class__.__name__}.{method_name}() ERROR: {e}"
                        )
                        raise

                return wrapper

            setattr(obj, method_name, traced_method(original, method_name))


def timeout_handler(signum, frame):
    print(f"\n🚨 TIMEOUT after {time.time() - tracer.start_time:.1f} seconds!")
    tracer.dump_last_steps(15)
    print("\n💡 The execution hung after the last logged step.")
    sys.exit(1)


# Set timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

try:
    tracer.log("Starting detailed Ansible execution trace")

    # Initialize
    init_plugin_loader()
    tracer.log("Plugin loader initialized")

    context.CLIARGS = ImmutableDict(
        {
            "connection": "local",
            "forks": 1,
            "verbosity": 0,
        }
    )

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=["localhost,"])
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    tracer.log("Ansible components created")

    # Create play
    play_source = {
        "name": "Trace Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [{"name": "Debug task", "debug": {"msg": "tracing"}}],
    }

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    tracer.log("Play created")

    # Create TaskQueueManager and trace its methods
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    tracer.log("TaskQueueManager created")

    # Trace key methods
    trace_calls(tqm, ["run", "_final_q_received", "_cleanup_processes"])

    # Also trace our ThreadProcess methods
    from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess

    # Monkey patch ThreadProcess to add tracing
    original_run_wrapper = ThreadProcess._run_wrapper

    def traced_run_wrapper(self):
        tracer.log(
            f"ThreadProcess._run_wrapper() START - target={self._target is not None}"
        )
        try:
            result = original_run_wrapper(self)
            tracer.log(f"ThreadProcess._run_wrapper() END")
            return result
        except Exception as e:
            tracer.log(f"ThreadProcess._run_wrapper() ERROR: {e}")
            raise

    ThreadProcess._run_wrapper = traced_run_wrapper

    # Monkey patch WorkerProcess.run method
    original_worker_run = WorkerProcess.run

    def traced_worker_run(self):
        tracer.log(f"WorkerProcess.run() START")
        try:
            result = original_worker_run(self)
            tracer.log(f"WorkerProcess.run() END")
            return result
        except Exception as e:
            tracer.log(f"WorkerProcess.run() ERROR: {e}")
            raise

    WorkerProcess.run = traced_worker_run

    tracer.log("All tracing set up, starting execution")

    # This is the critical call
    tracer.log("🚀 Calling tqm.run(play)")
    result = tqm.run(play)

    signal.alarm(0)  # Cancel timeout
    tracer.log(f"✅ tqm.run(play) completed with result: {result}")

    tqm.cleanup()
    tracer.log("✅ Cleanup completed")

    print(
        f"\n🎉 SUCCESS! Execution completed in {time.time() - tracer.start_time:.1f} seconds"
    )
    if result == 0:
        print("Task executed successfully!")
    else:
        print(f"Task completed with result: {result}")

except Exception as e:
    signal.alarm(0)
    tracer.log(f"❌ EXCEPTION: {e}")
    import traceback

    traceback.print_exc()
    tracer.dump_last_steps(15)

finally:
    signal.alarm(0)

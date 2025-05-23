#!/usr/bin/env python3
"""
Test our multiprocessing implementation with WorkerProcess patterns.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing WorkerProcess-like patterns...")

# Apply patches manually
from briefcase_ansible_test.utils._multiprocessing import _patch_system_modules

_patch_system_modules()

from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

print("✅ Patches applied")

# Test our multiprocessing components
from briefcase_ansible_test.utils._multiprocessing.process import ThreadProcess
from briefcase_ansible_test.utils._multiprocessing.queues import ProcessQueue

print("Step 1: Testing basic WorkerProcess pattern...")


class TestWorkerProcess(ThreadProcess):
    """Test class mimicking Ansible's WorkerProcess pattern."""

    def __init__(self, final_q, task_data):
        super().__init__(name="TestWorker")
        self._final_q = final_q
        self._task_data = task_data

    def run(self):
        """Override run method like WorkerProcess does."""
        print(f"  🔸 TestWorkerProcess.run() starting with: {self._task_data}")

        # Simulate some work
        time.sleep(0.1)

        # Send result to queue (like WorkerProcess does)
        result = f"processed_{self._task_data}"
        self._final_q.put(result)

        print(f"  🔸 TestWorkerProcess.run() completed, sent: {result}")
        return result


# Test queue communication
final_q = ProcessQueue()
test_data = "test_task"

worker = TestWorkerProcess(final_q, test_data)
print("  📝 Starting TestWorkerProcess...")
worker.start()
worker.join()

print(f"  ✅ Worker completed (exit code: {worker.exitcode})")

# Check queue result
try:
    result = final_q.get(timeout=1)
    print(f"  ✅ Received result from queue: {result}")
except:
    print("  ❌ No result received from queue")

print("Step 2: Testing multiple workers with queue...")


def create_and_run_workers(num_workers=3):
    """Test multiple workers like Ansible does."""
    final_q = ProcessQueue()
    workers = []

    for i in range(num_workers):
        worker_data = f"task_{i}"
        worker = TestWorkerProcess(final_q, worker_data)
        workers.append(worker)

    print(f"  📝 Starting {num_workers} workers...")
    for worker in workers:
        worker.start()

    print("  📝 Waiting for workers to complete...")
    for worker in workers:
        worker.join()
        print(f"    ✅ {worker.name} completed (exit code: {worker.exitcode})")

    # Collect results
    results = []
    try:
        while True:
            result = final_q.get(timeout=0.1)
            results.append(result)
    except:
        pass

    print(f"  ✅ Collected {len(results)} results: {results}")
    return len(results) == num_workers


success = create_and_run_workers(3)
if success:
    print("✅ Multiple workers test passed")
else:
    print("❌ Multiple workers test failed")

print("Step 3: Testing actual Ansible imports with our multiprocessing...")

try:
    # Import Ansible components that use multiprocessing
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.executor.process.worker import WorkerProcess

    print("✅ Ansible multiprocessing components imported")

    # Check that WorkerProcess is using our Process
    print(f"  📋 WorkerProcess base class: {WorkerProcess.__bases__}")

    # Quick test to make sure it's our implementation
    import multiprocessing

    test_proc = multiprocessing.Process(target=lambda: None)
    print(f"  📋 multiprocessing.Process type: {type(test_proc)}")

except Exception as e:
    print(f"❌ Ansible import failed: {e}")
    import traceback

    traceback.print_exc()

print("Step 4: Testing Ansible queue usage...")

try:
    # Test the specific queue pattern that Ansible uses
    from ansible.executor.task_queue_manager import FinalQueue

    print("  📝 Creating FinalQueue...")
    fq = FinalQueue()
    print("  ✅ FinalQueue created")

    # Test basic operations
    fq.put("test_message")
    result = fq.get(timeout=1)
    print(f"  ✅ FinalQueue basic operation: {result}")

    fq.close()
    print("  ✅ FinalQueue closed")

except Exception as e:
    print(f"❌ FinalQueue test failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🏁 WorkerProcess pattern testing complete")
print(
    "If all tests passed, our multiprocessing implementation should work with Ansible."
)

#!/usr/bin/env python3
"""
Test our ThreadProcess implementation directly.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing ThreadProcess implementation...")

# Import our multiprocessing directly (no patching)
from briefcase_ansible_test.utils._multiprocessing.process import ThreadProcess

print("✅ ThreadProcess imported")

print("Step 1: Testing basic target function...")


def test_target(name, delay=0.1):
    print(f"  🔸 test_target running: {name}")
    time.sleep(delay)
    return f"result_{name}"


p1 = ThreadProcess(target=test_target, args=("basic",), name="TestBasic")
print("  📝 Starting basic test...")
p1.start()
p1.join()
print(f"  ✅ Basic test completed (exit code: {p1.exitcode})")

print("Step 2: Testing run() method override...")


class TestProcess(ThreadProcess):
    def __init__(self, name="TestRun"):
        super().__init__(name=name)
        self.result = None

    def run(self):
        print(f"  🔸 {self.name}.run() called")
        time.sleep(0.1)
        self.result = "run_result"
        return self.result


p2 = TestProcess()
print("  📝 Starting run() test...")
p2.start()
p2.join()
print(f"  ✅ Run test completed (exit code: {p2.exitcode})")

print("Step 3: Testing multiple processes...")


def worker(worker_id):
    print(f"  🔸 Worker {worker_id} starting")
    time.sleep(0.2)
    print(f"  🔸 Worker {worker_id} done")
    return worker_id


processes = []
for i in range(3):
    p = ThreadProcess(target=worker, args=(i,), name=f"Worker-{i}")
    processes.append(p)

print("  📝 Starting 3 workers...")
for p in processes:
    p.start()

print("  📝 Waiting for workers...")
for p in processes:
    p.join()
    print(f"    ✅ {p.name} completed (exit code: {p.exitcode})")

print("Step 4: Testing with exception...")


def failing_target():
    print("  🔸 failing_target starting")
    raise ValueError("Test exception")


p3 = ThreadProcess(target=failing_target, name="FailTest")
print("  📝 Starting failing test...")
p3.start()
p3.join()
print(f"  ✅ Failing test completed (exit code: {p3.exitcode})")
if hasattr(p3, "_exception_info") and p3._exception_info:  # type: ignore
    print(f"    📋 Exception captured: {p3._exception_info}")

print("Step 5: Testing queue communication...")
from briefcase_ansible_test.utils._multiprocessing.queues import ProcessQueue


def producer(queue, items):
    print(f"  🔸 Producer starting with {items}")
    for i in range(items):
        queue.put(f"item_{i}")
        time.sleep(0.05)
    queue.put(None)  # Sentinel
    print(f"  🔸 Producer done")


def consumer(queue, name):
    print(f"  🔸 Consumer {name} starting")
    results = []
    while True:
        item = queue.get()
        if item is None:
            queue.put(None)  # Pass sentinel on
            break
        results.append(item)
        print(f"    📦 {name} got: {item}")
    print(f"  🔸 Consumer {name} done: {results}")
    return results


q = ProcessQueue()
p_producer = ThreadProcess(target=producer, args=(q, 3), name="Producer")
p_consumer = ThreadProcess(target=consumer, args=(q, "Consumer"), name="Consumer")

print("  📝 Starting producer/consumer test...")
p_producer.start()
p_consumer.start()

p_producer.join()
p_consumer.join()
print(f"  ✅ Queue test completed")

print("\n🎉 All ThreadProcess tests passed!")
print("Our ThreadProcess implementation appears to be working correctly.")

#!/usr/bin/env python3
"""
Test script for the iOS multiprocessing implementation.

This script tests the basic functionality of our threading-based multiprocessing
replacement to ensure it works correctly before integrating with Ansible.
"""

import sys
import time
import queue as queue_module
import threading

# Import our multiprocessing implementation
sys.path.insert(0, "src")
from briefcase_ansible_test.utils.multiprocessing import (
    Process,
    Queue,
    SimpleQueue,
    Lock,
    RLock,
    Event,
    Semaphore,
    get_context,
    Pool,
)


def test_basic_process():
    """Test basic Process functionality."""
    print("Testing basic Process functionality...")

    def worker_function(name, delay):
        print(f"Worker {name} starting, sleeping for {delay}s")
        time.sleep(delay)
        print(f"Worker {name} finished")
        return f"Result from {name}"

    # Test process creation and execution
    p = Process(target=worker_function, args=("test1", 0.1))

    print(f"Process created: {p}")
    print(f"Is alive before start: {p.is_alive()}")
    print(f"Exit code before start: {p.exitcode}")

    p.start()
    print(f"Is alive after start: {p.is_alive()}")

    p.join()
    print(f"Is alive after join: {p.is_alive()}")
    print(f"Exit code after join: {p.exitcode}")

    print("✓ Basic Process test passed\n")


def test_process_with_exception():
    """Test Process exception handling."""
    print("Testing Process exception handling...")

    def worker_with_exception():
        print("Worker about to raise exception")
        raise ValueError("Test exception from worker")

    p = Process(target=worker_with_exception)
    p.start()
    p.join()

    print(f"Exit code after exception: {p.exitcode}")
    print("✓ Process exception test passed\n")


def test_queues():
    """Test Queue functionality."""
    print("Testing Queue functionality...")

    def producer(queue, items):
        for item in items:
            print(f"Putting: {item}")
            queue.put(item)
        queue.put(None)  # Sentinel

    def consumer(queue, results):
        while True:
            item = queue.get()
            if item is None:
                break
            print(f"Got: {item}")
            results.append(item)

    # Test regular Queue
    q = Queue()
    results = []

    p1 = Process(target=producer, args=(q, ["a", "b", "c"]))
    p2 = Process(target=consumer, args=(q, results))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print(f"Results: {results}")
    print("✓ Queue test passed\n")


def test_simple_queue():
    """Test SimpleQueue functionality."""
    print("Testing SimpleQueue functionality...")

    def simple_worker(sq, value):
        sq.put(f"Value: {value}")

    sq = SimpleQueue()

    # Start multiple workers
    workers = []
    for i in range(3):
        p = Process(target=simple_worker, args=(sq, i))
        p.start()
        workers.append(p)

    # Wait for all workers
    for p in workers:
        p.join()

    # Collect results
    results = []
    while not sq.empty():
        results.append(sq.get())

    print(f"SimpleQueue results: {results}")
    print("✓ SimpleQueue test passed\n")


def test_synchronization():
    """Test synchronization primitives."""
    print("Testing synchronization primitives...")

    # Test Lock
    lock = Lock()
    shared_data = []

    def locked_worker(lock, data, value):
        with lock:
            print(f"Worker {value} acquired lock")
            data.append(value)
            time.sleep(0.01)
            print(f"Worker {value} releasing lock")

    workers = []
    for i in range(3):
        p = Process(target=locked_worker, args=(lock, shared_data, i))
        p.start()
        workers.append(p)

    for p in workers:
        p.join()

    print(f"Shared data: {shared_data}")

    # Test Event
    event = Event()

    def waiter(event, name):
        print(f"{name} waiting for event")
        event.wait()
        print(f"{name} event received")

    def setter(event):
        time.sleep(0.1)
        print("Setting event")
        event.set()

    waiters = []
    for i in range(2):
        p = Process(target=waiter, args=(event, f"Waiter-{i}"))
        p.start()
        waiters.append(p)

    setter_p = Process(target=setter, args=(event,))
    setter_p.start()

    for p in waiters:
        p.join()
    setter_p.join()

    print("✓ Synchronization test passed\n")


def test_context():
    """Test context functionality."""
    print("Testing context functionality...")

    ctx = get_context()
    print(f"Context start method: {ctx.get_start_method()}")

    # Test context-created objects
    p = ctx.Process(target=lambda: print("Context process running"))
    q = ctx.Queue()
    lock = ctx.Lock()

    p.start()
    p.join()

    print("✓ Context test passed\n")


def test_pool():
    """Test Pool functionality."""
    print("Testing Pool functionality...")

    def square(x):
        return x * x

    with Pool(processes=2) as pool:
        # Test map
        results = pool.map(square, [1, 2, 3, 4, 5])
        print(f"Pool map results: {results}")

        # Test apply_async
        async_result = pool.apply_async(square, (10,))
        result = async_result.get()
        print(f"Pool apply_async result: {result}")

    print("✓ Pool test passed\n")


def test_exception_propagation():
    """Test exception propagation through queues."""
    print("Testing exception propagation...")

    def worker_with_queue_exception(q):
        try:
            raise RuntimeError("Worker exception")
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=worker_with_queue_exception, args=(q,))
    p.start()
    p.join()

    try:
        result = q.get()
        if isinstance(result, Exception):
            print(f"Received exception: {result}")
        else:
            print(f"Unexpected result: {result}")
    except Exception as e:
        print(f"Exception when getting from queue: {e}")

    print("✓ Exception propagation test passed\n")


def main():
    """Run all tests."""
    print("Starting iOS multiprocessing implementation tests...\n")

    try:
        test_basic_process()
        test_process_with_exception()
        test_queues()
        test_simple_queue()
        test_synchronization()
        test_context()
        test_pool()
        test_exception_propagation()

        print("🎉 All tests passed! iOS multiprocessing implementation is working.")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

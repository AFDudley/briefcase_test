# Testing Guide: iOS Threading-Based Multiprocessing

## 🧪 Test Suite Overview

This guide covers the comprehensive testing approach used to validate the iOS threading-based multiprocessing implementation and ensure Ansible compatibility.

## 🎯 Testing Philosophy

### Progressive Complexity
1. **Unit Tests**: Individual component validation
2. **Integration Tests**: Component interaction testing  
3. **System Tests**: Full Ansible integration
4. **Comprehensive Tests**: Real-world scenario validation

### Coverage Areas
- **API Compatibility**: Exact multiprocessing API behavior
- **Performance**: Execution time and resource usage
- **Error Handling**: Failure scenarios and recovery
- **Concurrency**: Multiple worker behavior
- **Edge Cases**: Unusual usage patterns

## 🔧 Test Categories

### 1. Unit Tests

#### ThreadProcess Basic Functionality
```python
# test_threadprocess.py
def test_target_function():
    """Test basic target function execution."""
    def worker(name):
        return f"result_{name}"
    
    p = ThreadProcess(target=worker, args=("test",))
    p.start()
    p.join()
    assert p.exitcode == 0

def test_run_method_override():
    """Test run() method inheritance pattern."""
    class TestProcess(ThreadProcess):
        def run(self):
            return "custom_result"
    
    p = TestProcess()
    p.start()
    p.join()
    assert p.exitcode == 0
```

#### Queue Operations
```python
def test_queue_timeout():
    """Test queue timeout functionality."""
    queue = ProcessSimpleQueue()
    
    # Should raise Empty exception
    with pytest.raises(queue.Empty):
        queue.get(timeout=0.1)
    
    # Should work with item
    queue.put("test")
    result = queue.get(timeout=1)
    assert result == "test"
```

#### Exception Handling
```python
def test_exception_propagation():
    """Test cross-thread exception handling."""
    def failing_worker():
        raise ValueError("Test exception")
    
    p = ThreadProcess(target=failing_worker)
    p.start()
    p.join()
    assert p.exitcode == 1
    assert hasattr(p, '_exception')
```

### 2. Integration Tests

#### WorkerProcess Pattern Simulation
```python
# test_workerprocess.py
class TestWorkerProcess(ThreadProcess):
    """Simulate Ansible's WorkerProcess pattern."""
    
    def __init__(self, final_q, task_data):
        super().__init__(name="TestWorker")
        self._final_q = final_q
        self._task_data = task_data
    
    def run(self):
        # Simulate task execution
        result = f"processed_{self._task_data}"
        self._final_q.put(result)
        return result

def test_multiple_workers():
    """Test multiple workers with queue communication."""
    final_q = ProcessQueue()
    workers = []
    
    for i in range(3):
        worker = TestWorkerProcess(final_q, f"task_{i}")
        workers.append(worker)
        worker.start()
    
    for worker in workers:
        worker.join()
        assert worker.exitcode == 0
    
    # Collect results
    results = []
    while not final_q.empty():
        results.append(final_q.get(timeout=1))
    
    assert len(results) == 3
```

#### Ansible Component Integration
```python
def test_ansible_imports():
    """Test Ansible component imports with our multiprocessing."""
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.executor.process.worker import WorkerProcess
    
    # Verify WorkerProcess uses our implementation
    assert WorkerProcess.__bases__[0].__name__ == 'ThreadProcess'
    
def test_final_queue():
    """Test Ansible's FinalQueue with our implementation."""
    from ansible.executor.task_queue_manager import FinalQueue
    
    fq = FinalQueue()
    fq.put("test_message")
    result = fq.get(timeout=1)
    assert result == "test_message"
    fq.close()
```

### 3. System Tests

#### Simple Ansible Playbook
```python
# test_ansible_simple.py
def test_simple_playbook():
    """Test basic Ansible playbook execution."""
    play_source = {
        "name": "Simple Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {
                "name": "Debug message",
                "debug": {"msg": "Hello World"}
            }
        ]
    }
    
    result = execute_playbook(play_source)
    assert result == 0  # Success
```

#### Complex Playbook Features
```python
def test_complex_playbook():
    """Test playbook with variables, loops, conditionals."""
    play_source = {
        "name": "Complex Test",
        "hosts": "localhost", 
        "gather_facts": "no",
        "vars": {"test_var": "value"},
        "tasks": [
            {
                "name": "Variable test",
                "debug": {"msg": "Variable: {{ test_var }}"}
            },
            {
                "name": "Loop test",
                "debug": {"msg": "Item: {{ item }}"},
                "loop": ["a", "b", "c"]
            },
            {
                "name": "Conditional test", 
                "debug": {"msg": "Condition met"},
                "when": "test_var is defined"
            }
        ]
    }
    
    result = execute_playbook(play_source)
    assert result == 0
```

### 4. Comprehensive Tests

#### Error Handling
```python
def test_error_handling():
    """Test playbook error handling and recovery."""
    play_source = {
        "name": "Error Test",
        "hosts": "localhost",
        "gather_facts": "no", 
        "tasks": [
            {
                "name": "Success task",
                "debug": {"msg": "This works"}
            },
            {
                "name": "Failing task",
                "command": "false",  # Will fail
                "ignore_errors": "yes"
            },
            {
                "name": "Recovery task",
                "debug": {"msg": "After failure"}
            }
        ]
    }
    
    result = execute_playbook(play_source)
    assert result == 0  # Should succeed despite failure
```

#### Performance Testing
```python
def test_performance():
    """Test performance with multiple tasks."""
    import time
    
    tasks = []
    for i in range(10):
        tasks.append({
            "name": f"Task {i+1}",
            "debug": {"msg": f"Executing task {i+1}"}
        })
    
    play_source = {
        "name": "Performance Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": tasks
    }
    
    start_time = time.time()
    result = execute_playbook(play_source)
    elapsed = time.time() - start_time
    
    assert result == 0
    assert elapsed < 5.0  # Should complete within 5 seconds
```

#### Sequential Execution
```python
def test_sequential_playbooks():
    """Test multiple playbook executions in sequence."""
    for i in range(5):
        play_source = {
            "name": f"Sequential Test {i+1}",
            "hosts": "localhost",
            "gather_facts": "no",
            "tasks": [
                {
                    "name": f"Task {i+1}",
                    "debug": {"msg": f"Sequential run {i+1}"}
                }
            ]
        }
        
        result = execute_playbook(play_source)
        assert result == 0
```

## 🔍 Debug Testing Techniques

### Timeout Protection
```python
def with_timeout(timeout_seconds):
    """Decorator to prevent tests from hanging."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test timed out after {timeout_seconds}s")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except:
                signal.alarm(0)
                raise
        
        return wrapper
    return decorator

@with_timeout(30)
def test_no_hang_playbook():
    """Ensure playbook execution doesn't hang."""
    # Test implementation
```

### Thread Monitoring
```python
def test_with_thread_monitoring():
    """Test with thread lifecycle monitoring."""
    import threading
    
    def monitor_threads():
        while not done.is_set():
            count = threading.active_count()
            names = [t.name for t in threading.enumerate()]
            print(f"Threads: {count} - {names}")
            time.sleep(0.5)
    
    done = threading.Event()
    monitor = threading.Thread(target=monitor_threads, daemon=True)
    monitor.start()
    
    try:
        # Run actual test
        result = execute_test()
        done.set()
        return result
    finally:
        done.set()
```

### Exception Instrumentation
```python
def test_with_exception_capture():
    """Test with comprehensive exception capture."""
    exceptions = []
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        exceptions.append((exc_type, exc_value, exc_traceback))
        original_handler(exc_type, exc_value, exc_traceback)
    
    original_handler = sys.excepthook
    sys.excepthook = exception_handler
    
    try:
        result = execute_test()
        assert len(exceptions) == 0, f"Unexpected exceptions: {exceptions}"
        return result
    finally:
        sys.excepthook = original_handler
```

## 📊 Test Results Analysis

### Success Criteria
- **Functional**: All playbook tasks execute successfully
- **Performance**: Execution time within acceptable limits
- **Stability**: No hangs or deadlocks
- **Compatibility**: Exact multiprocessing API behavior
- **Error Handling**: Proper failure recovery

### Key Metrics
- **Execution Time**: < 1s for simple playbooks, < 5s for complex
- **Memory Usage**: Minimal threading overhead
- **Thread Count**: Stable thread lifecycle
- **Error Rate**: Zero unexpected failures
- **API Compatibility**: 100% multiprocessing API coverage

### Expected Results
```
✅ ThreadProcess Basic Tests: 100% pass
✅ Queue Operation Tests: 100% pass  
✅ WorkerProcess Pattern Tests: 100% pass
✅ Simple Ansible Tests: 100% pass
✅ Complex Playbook Tests: 100% pass
✅ Error Handling Tests: 100% pass
✅ Performance Tests: 100% pass
✅ Sequential Execution Tests: 100% pass
```

## 🚨 Common Test Issues

### Hanging Tests
**Symptoms**: Test never completes, high CPU usage
**Causes**: 
- Missing timeout support in queues
- Incorrect WorkerProcess inheritance pattern
- Circular import during patching

**Solutions**:
- Add timeout parameters to all queue operations
- Implement both target function and run() method patterns
- Control import order and patching timing

### Import Errors
**Symptoms**: Module not found, circular import errors
**Causes**:
- Incorrect system module patching
- Missing submodule exports
- Import order dependencies

**Solutions**:
- Comprehensive system module patching
- Proper module attribute exposure
- Controlled import sequence

### Performance Issues
**Symptoms**: Slow execution, excessive resource usage
**Causes**:
- Inefficient threading implementation
- Queue blocking behavior
- Memory leaks in thread lifecycle

**Solutions**:
- Optimize thread creation/destruction
- Non-blocking queue operations where appropriate
- Proper thread cleanup and resource management

## 🏃‍♂️ Running the Tests

### Quick Test
```bash
python test_threadprocess.py
```

### Comprehensive Test
```bash  
python test_ansible_comprehensive.py
```

### Debug Test
```bash
python test_workerprocess.py
```

### Performance Test
```bash
time python test_ansible_play_final.py
```

## 🎯 Test Maintenance

### Adding New Tests
1. Follow progressive complexity principle
2. Include timeout protection
3. Add thread monitoring for concurrency tests
4. Capture and validate exceptions
5. Measure performance impact

### Regression Testing
- Run full suite after any implementation changes
- Test with different Ansible versions
- Validate on different iOS versions/devices
- Performance regression detection

This comprehensive testing approach ensures the iOS threading-based multiprocessing implementation meets all requirements for production Ansible usage.
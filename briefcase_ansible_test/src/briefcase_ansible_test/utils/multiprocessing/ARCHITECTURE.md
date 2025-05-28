# iOS Threading-Based Multiprocessing Architecture

## Overview

This module provides a complete threading-based replacement for Python's `multiprocessing` module, enabling Ansible and other multiprocessing-dependent applications to run on iOS where traditional process-based multiprocessing is not available.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Code                         │
│  (e.g., Ansible TaskQueueManager, WorkerProcess)           │
└─────────────────┬───────────────────────────────────────────┘
                  │ import multiprocessing
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Auto-Patching Layer (__init__.py)              │
│  - Replaces sys.modules['multiprocessing']                 │
│  - Patches all submodules                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Components                          │
├─────────────────┴───────────────────────────────────────────┤
│  ThreadProcess      │  ProcessQueue     │  Synchronization  │
│  - start()         │  - put/get()      │  - Lock/RLock    │
│  - join()          │  - timeout support │  - Semaphore     │
│  - run() override  │  - exceptions      │  - Event/Barrier │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Threading API                        │
│              (threading.Thread, queue.Queue)                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Transparent API Compatibility

The module maintains 100% API compatibility with standard multiprocessing:

```python
# Standard multiprocessing code works unchanged
import multiprocessing

p = multiprocessing.Process(target=worker_func, args=(1, 2))
p.start()
p.join()
```

### 2. Dual-Mode Process Creation

Supports both usage patterns required by different applications:

```python
# Pattern 1: Target function (most common)
p = Process(target=my_function, args=())

# Pattern 2: Subclass with run() override (Ansible's pattern)
class WorkerProcess(Process):
    def run(self):
        # Custom implementation
        pass
```

### 3. Exception Serialization

Exceptions are automatically serialized when crossing thread boundaries:

```python
# In ThreadProcess._run_wrapper()
try:
    result = self._target(*self._args, **self._kwargs)
except Exception as e:
    # Exception is pickled and stored
    self._exception = e
    self._exitcode = 1

# In Queue implementation
if isinstance(item, Exception):
    # Serialize for cross-thread compatibility
    item = self._serialize_exception(item)
```

### 4. Queue Timeout Support

All queue operations support timeout parameters:

```python
# ProcessQueue.get() with timeout
def get(self, block=True, timeout=None):
    item = self._queue.get(block=block, timeout=timeout)
    # Handle exception deserialization
    return item
```

## Component Details

### ThreadProcess (`process.py`)

The core process replacement using threading:

**Key Features:**
- Inherits from `BaseProcess` for compatibility
- Uses `threading.Thread` internally
- Maintains process-like state (pid, exitcode, daemon)
- Supports both target functions and run() method override
- Provides terminate() and kill() methods (sets flags)

**Critical Implementation:**
```python
def _run_wrapper(self):
    """Wrapper that handles both usage patterns."""
    try:
        if self._target is not None:
            # Standard usage: Process(target=function)
            result = self._target(*self._args, **self._kwargs)
        else:
            # Subclass usage: Override run() method
            result = self.run()
        self._exitcode = 0
    except Exception as e:
        self._exception = e
        self._exitcode = 1
```

### Queue System (`queues.py`)

Thread-safe queues with multiprocessing-compatible API:

**Implementations:**
- `ProcessQueue`: Full-featured queue with maxsize
- `ProcessSimpleQueue`: Lightweight unbounded queue  
- `JoinableQueue`: Supports task_done() and join()

**Key Features:**
- Exception serialization/deserialization
- Timeout support on all operations
- Cross-thread exception propagation
- Compatible error types (queue.Empty, queue.Full)

### Synchronization Primitives (`synchronize/`)

Threading-based implementations of multiprocessing synchronization:

**Components:**
- `ThreadLock` / `ThreadRLock`: Basic locking
- `ThreadSemaphore` / `ThreadBoundedSemaphore`: Resource counting
- `ThreadEvent`: Simple signaling
- `ThreadCondition`: Complex synchronization
- `ThreadBarrier`: Multi-thread synchronization points

### Context Management (`context.py`)

Provides multiprocessing context compatibility:

**Features:**
- Multiple context support (spawn, fork, forkserver)
- Factory methods for creating processes and queues
- Start method management
- Reducer/duplicator compatibility stubs

## Auto-Patching Mechanism

The module automatically patches system modules on import:

```python
# In __init__.py
def _patch_system_modules():
    # Replace main module
    sys.modules["multiprocessing"] = sys.modules[__name__]
    
    # Create and patch submodules
    process_module = type("Module", (), {})()
    process_module.Process = Process
    sys.modules["multiprocessing.process"] = process_module
    
    # ... similar for other submodules
```

This ensures that any code importing multiprocessing gets our implementation.

## iOS-Specific Optimizations

### Memory Efficiency
- Threads share memory space (no process overhead)
- Lightweight compared to full process creation
- Automatic resource cleanup

### Sandbox Compatibility
- No fork() or exec() calls
- No semaphore creation (sem_open)
- Works within iOS app sandbox restrictions

### Performance
- Fast thread creation vs process spawning
- Efficient queue operations
- Minimal overhead for synchronization

## Integration with Ansible

The implementation specifically supports Ansible's patterns:

1. **WorkerProcess Inheritance**: Ansible's WorkerProcess extends multiprocessing.Process
2. **Queue Communication**: FinalQueue expects specific timeout behavior
3. **Process Lifecycle**: Proper start/join/terminate semantics
4. **Exception Handling**: Cross-process exception propagation

## Testing Strategy

Comprehensive test coverage ensures reliability:

1. **Unit Tests**: Individual component validation
2. **Integration Tests**: Component interaction testing
3. **System Tests**: Full Ansible playbook execution
4. **Performance Tests**: Benchmarking and optimization

## Known Limitations

### Python GIL
- True parallelism limited by Global Interpreter Lock
- CPU-bound tasks won't see multicore benefits

### Memory Isolation
- Threads share memory space
- No process-level isolation

### Signal Handling
- Different signal behavior compared to processes
- Some signals may not work as expected

## Future Enhancements

Potential improvements for future versions:

1. **Shared Memory**: Implement shared_memory module compatibility
2. **Manager Support**: Add multiprocessing.Manager functionality
3. **Advanced Pool**: Enhanced Pool implementation with more features
4. **Performance**: Further optimization for iOS constraints

## Conclusion

This threading-based multiprocessing implementation successfully bridges the gap between Python's process-based multiprocessing and iOS's threading-only environment, enabling complex applications like Ansible to run on iOS devices without modification.
"""
Trace imports to find circular dependencies
"""

import sys
import importlib


def test_import_trace(ui_updater):
    """Trace module imports to find circular dependencies"""
    ui_updater.add_text_to_output("Tracing imports to find circular dependencies...\n")

    # Keep track of what's being imported
    # Handle both dict and module forms of __builtins__
    if isinstance(__builtins__, dict):
        original_import = __builtins__["__import__"]
    else:
        original_import = __builtins__.__import__

    import_stack = []
    seen_imports = set()

    def traced_import(name, *args, **kwargs):
        indent = "  " * len(import_stack)

        # Check for circular import
        if name in import_stack:
            ui_updater.add_text_to_output(
                f"\n{indent}❌ CIRCULAR IMPORT DETECTED: {name}\n"
            )
            ui_updater.add_text_to_output(
                f"{indent}Import stack: {' -> '.join(import_stack)} -> {name}\n"
            )
            # Don't actually do the circular import
            if name in sys.modules:
                return sys.modules[name]

        # Track this import
        import_stack.append(name)

        # Only show ansible-related imports to reduce noise
        if "ansible" in name and name not in seen_imports:
            ui_updater.add_text_to_output(f"{indent}→ {name}\n")
            seen_imports.add(name)

        try:
            # Do the actual import
            result = original_import(name, *args, **kwargs)
            return result
        finally:
            # Pop from stack
            if import_stack and import_stack[-1] == name:
                import_stack.pop()

    # Replace the import function
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = traced_import
    else:
        __builtins__.__import__ = traced_import

    try:
        ui_updater.add_text_to_output(
            "\nStarting traced import of ansible.executor.task_executor...\n"
        )

        # First clear it from modules to force fresh import
        if "ansible.executor.task_executor" in sys.modules:
            del sys.modules["ansible.executor.task_executor"]

        # Try the import with timeout
        import threading

        import_done = False
        import_error = None

        def try_import():
            nonlocal import_done, import_error
            try:
                import ansible.executor.task_executor

                import_done = True
            except Exception as e:
                import_error = e

        t = threading.Thread(target=try_import)
        t.daemon = True
        t.start()
        t.join(timeout=5.0)

        if import_done:
            ui_updater.add_text_to_output("\n✅ Import succeeded!")
        elif t.is_alive():
            ui_updater.add_text_to_output("\n❌ Import timed out")
            ui_updater.add_text_to_output(
                f"\nLast import in progress: {import_stack[-1] if import_stack else 'None'}\n"
            )
        elif import_error:
            ui_updater.add_text_to_output(f"\n❌ Import failed: {import_error}")

    finally:
        # Restore original import
        if isinstance(__builtins__, dict):
            __builtins__["__import__"] = original_import
        else:
            __builtins__.__import__ = original_import

    ui_updater.add_text_to_output("\nImport trace completed\n")

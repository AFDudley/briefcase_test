"""
Test importing task_executor directly with timeout
"""

import threading
import time


def test_direct_import(ui_updater):
    """Test importing task_executor directly"""
    ui_updater.add_text_to_output(
        "Testing direct import of task_executor with timeout...\n"
    )

    import_success = False
    import_error = None

    def try_import():
        nonlocal import_success, import_error
        try:
            ui_updater.add_text_to_output(
                "Attempting to import ansible.executor.task_executor...\n"
            )
            import ansible.executor.task_executor

            import_success = True
            ui_updater.add_text_to_output("✅ Import successful!\n")
        except Exception as e:
            import_error = e
            ui_updater.add_text_to_output(f"❌ Import failed: {e}\n")

    # Run import in a thread with timeout
    import_thread = threading.Thread(target=try_import)
    import_thread.daemon = True
    import_thread.start()

    # Wait up to 5 seconds
    import_thread.join(timeout=5.0)

    if import_thread.is_alive():
        ui_updater.add_text_to_output(
            "❌ Import timed out after 5 seconds - module is hanging during import\n"
        )
        ui_updater.add_text_to_output(
            "\nThis confirms the hang is in the module-level initialization code.\n"
        )
    elif import_success:
        ui_updater.add_text_to_output("Import completed successfully - no hang!\n")
    elif import_error:
        ui_updater.add_text_to_output(f"Import failed with error: {import_error}\n")

    ui_updater.add_text_to_output("\nDirect import test completed\n")

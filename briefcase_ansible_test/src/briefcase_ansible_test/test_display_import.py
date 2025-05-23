"""
Test importing Display and related modules to debug the hang
"""


def test_display_import(ui_updater):
    """Test if we can import Display and its dependencies"""
    ui_updater.add_text_to_output("Testing Display import and dependencies...\n")

    # Test potentially problematic imports
    modules_to_test = [
        ("curses", "Terminal control library"),
        ("fcntl", "File control operations"),
        ("termios", "Terminal I/O settings"),
        ("tty", "Terminal control functions"),
        ("subprocess", "Process spawning"),
    ]

    ui_updater.add_text_to_output("\nTesting system modules:\n")
    for module_name, description in modules_to_test:
        ui_updater.add_text_to_output(f"  - {module_name} ({description})... ")
        try:
            module = __import__(module_name)
            ui_updater.add_text_to_output(f"✅ {module}\n")
        except ImportError as e:
            ui_updater.add_text_to_output(f"❌ ImportError: {e}\n")
        except Exception as e:
            ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}\n")

    # Try to import Display
    ui_updater.add_text_to_output("\nTrying to import ansible.utils.display...\n")
    try:
        import ansible.utils.display

        ui_updater.add_text_to_output(
            f"✅ ansible.utils.display imported: {ansible.utils.display}\n"
        )

        from ansible.utils.display import Display

        ui_updater.add_text_to_output(f"✅ Display class imported: {Display}\n")

        # Try to create a Display instance
        display = Display()
        ui_updater.add_text_to_output(f"✅ Display instance created: {display}\n")

    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Failed to import Display: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Now test task_executor import directly
    ui_updater.add_text_to_output(
        "\nTrying to import ansible.executor.task_executor...\n"
    )
    try:
        import ansible.executor.task_executor

        ui_updater.add_text_to_output(
            f"✅ ansible.executor.task_executor imported: {ansible.executor.task_executor}\n"
        )

        from ansible.executor.task_executor import TaskExecutor

        ui_updater.add_text_to_output(
            f"✅ TaskExecutor class imported: {TaskExecutor}\n"
        )

    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Failed to import task_executor: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    ui_updater.add_text_to_output("\nDisplay import test completed\n")

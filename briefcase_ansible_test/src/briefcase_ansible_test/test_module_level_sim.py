"""
Simulate the exact module-level code from task_executor.py
"""


def test_module_level_sim(ui_updater):
    """Simulate module-level initialization from task_executor"""
    ui_updater.add_text_to_output("Simulating task_executor module-level code...\n")

    # Step 1: Import constants
    ui_updater.add_text_to_output("\nStep 1: Importing constants... ")
    try:
        from ansible import constants as C

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {e}")
        return

    # Step 2: Import Display
    ui_updater.add_text_to_output("\nStep 2: Importing Display... ")
    try:
        from ansible.utils.display import Display

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {e}")
        return

    # Step 3: Create display instance (line 37 in task_executor.py)
    ui_updater.add_text_to_output("\nStep 3: Creating display = Display()... ")
    try:
        display = Display()
        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {e}")
        return

    # Step 4: Create RETURN_VARS (line 40 in task_executor.py)
    ui_updater.add_text_to_output("\nStep 4: Creating RETURN_VARS list... ")
    try:
        RETURN_VARS = [
            x
            for x in C.MAGIC_VARIABLE_MAPPING.items()
            if "become" not in x and "_pass" not in x
        ]
        ui_updater.add_text_to_output(f"✅ ({len(RETURN_VARS)} items)")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {e}")
        return

    # Step 5: Define CLI_STUB_NAME constant
    ui_updater.add_text_to_output("\nStep 5: Setting CLI_STUB_NAME... ")
    try:
        CLI_STUB_NAME = "ansible_connection_cli_stub.py"
        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {e}")
        return

    # If we get here, all module-level code executed successfully
    ui_updater.add_text_to_output("\n\n✅ All module-level code executed successfully!")
    ui_updater.add_text_to_output(
        "\nThe hang must be happening during import processing, not in the code itself.\n"
    )

    # Now let's try the actual import one more time
    ui_updater.add_text_to_output(
        "\nAttempting actual import of ansible.executor.task_executor...\n"
    )
    ui_updater.add_text_to_output(
        "(This may hang if there's an import cycle or other issue)\n"
    )

    import threading

    import_done = False

    def try_import():
        nonlocal import_done
        try:
            import ansible.executor.task_executor

            import_done = True
        except:
            pass

    t = threading.Thread(target=try_import)
    t.daemon = True
    t.start()
    t.join(timeout=3.0)

    if import_done:
        ui_updater.add_text_to_output("✅ Import succeeded!")
    else:
        ui_updater.add_text_to_output(
            "❌ Import timed out - confirming hang during import"
        )

    ui_updater.add_text_to_output("\n\nModule-level simulation test completed\n")

"""
Test importing ansible.cli to see what causes the hang
"""

import sys
import threading


def test_cli_import(ui_updater):
    """Test importing ansible.cli and its submodules"""
    ui_updater.add_text_to_output("Testing ansible.cli import...\n")

    # First check if it's already imported
    if "ansible.cli" in sys.modules:
        ui_updater.add_text_to_output("Note: ansible.cli is already in sys.modules\n")

    # Test basic import with timeout
    ui_updater.add_text_to_output("\nTrying to import ansible.cli with timeout...\n")

    import_success = False
    import_error = None

    def try_import():
        nonlocal import_success, import_error
        try:
            import ansible.cli

            import_success = True
        except Exception as e:
            import_error = e

    t = threading.Thread(target=try_import)
    t.daemon = True
    t.start()
    t.join(timeout=3.0)

    if t.is_alive():
        ui_updater.add_text_to_output("❌ Import timed out - ansible.cli is hanging\n")

        # Now let's check what ansible.cli is trying to do
        ui_updater.add_text_to_output("\nChecking ansible.cli dependencies...\n")

        # Common CLI-related imports that might be problematic
        cli_deps = [
            ("argparse", "Argument parsing"),
            ("getpass", "Password input"),
            ("sys", "System module"),
            ("os", "OS module"),
            ("ansible.cli.arguments", "CLI arguments"),
            ("ansible.utils.display", "Display"),
            ("ansible.utils.cmd_functions", "Command functions"),
        ]

        for mod, desc in cli_deps:
            ui_updater.add_text_to_output(f"  Testing {mod} ({desc})... ")
            try:
                __import__(mod)
                ui_updater.add_text_to_output("✅\n")
            except Exception as e:
                ui_updater.add_text_to_output(f"❌ {e}\n")

    elif import_success:
        ui_updater.add_text_to_output("✅ Import succeeded!\n")
    elif import_error:
        ui_updater.add_text_to_output(f"❌ Import failed: {import_error}\n")

    # Let's also check if the issue is with specific CLI submodules
    ui_updater.add_text_to_output("\nTesting specific CLI submodules...\n")

    cli_submodules = [
        "ansible.cli.arguments",
        "ansible.cli.galaxy",
        "ansible.cli.playbook",
        "ansible.cli.vault",
    ]

    for submod in cli_submodules:
        if submod in sys.modules:
            ui_updater.add_text_to_output(f"  {submod}: Already loaded\n")
            continue

        ui_updater.add_text_to_output(f"  {submod}: ")

        import_ok = False

        def try_subimport():
            nonlocal import_ok
            try:
                __import__(submod)
                import_ok = True
            except:
                pass

        st = threading.Thread(target=try_subimport)
        st.daemon = True
        st.start()
        st.join(timeout=1.0)

        if import_ok:
            ui_updater.add_text_to_output("✅\n")
        elif st.is_alive():
            ui_updater.add_text_to_output("❌ Timed out\n")
        else:
            ui_updater.add_text_to_output("❌ Failed\n")

    ui_updater.add_text_to_output("\nCLI import test completed\n")

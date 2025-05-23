"""
Test signal handling to understand iOS termination
"""

import signal
import threading
import time
import os


def test_signal_handling(ui_updater):
    """Test signal handling on iOS"""
    ui_updater.add_text_to_output("Testing signal handling...\n")

    # Check current signal handlers
    ui_updater.add_text_to_output("\nCurrent signal handlers:\n")
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGCHLD]:
        try:
            handler = signal.signal(sig, signal.SIG_DFL)
            signal.signal(sig, handler)  # Restore
            ui_updater.add_text_to_output(f"  {sig.name}: {handler}\n")
        except Exception as e:
            ui_updater.add_text_to_output(f"  {sig.name}: Error - {e}\n")

    # Test if we can install signal handlers
    ui_updater.add_text_to_output("\nTesting signal handler installation:\n")

    signal_received = threading.Event()

    def signal_handler(signum, frame):
        ui_updater.add_text_to_output(
            f"\n!!! Received signal {signum} ({signal.Signals(signum).name})\n"
        )
        ui_updater.add_text_to_output(f"Frame: {frame}\n")
        signal_received.set()

    # Try to install handlers
    for sig in [signal.SIGTERM, signal.SIGUSR1]:
        try:
            old_handler = signal.signal(sig, signal_handler)
            ui_updater.add_text_to_output(f"  ✅ Installed handler for {sig.name}\n")
            signal.signal(sig, old_handler)  # Restore
        except Exception as e:
            ui_updater.add_text_to_output(
                f"  ❌ Cannot install handler for {sig.name}: {e}\n"
            )

    # Test os.fork() availability
    ui_updater.add_text_to_output("\nTesting os.fork():\n")
    try:
        if hasattr(os, "fork"):
            ui_updater.add_text_to_output("  os.fork exists\n")
            # Don't actually call it - just check existence
        else:
            ui_updater.add_text_to_output("  os.fork does NOT exist\n")
    except Exception as e:
        ui_updater.add_text_to_output(f"  Error checking fork: {e}\n")

    # Test subprocess
    ui_updater.add_text_to_output("\nTesting subprocess module:\n")
    try:
        import subprocess

        ui_updater.add_text_to_output("  ✅ subprocess imported\n")

        # Try a simple command
        try:
            result = subprocess.run(
                ["echo", "test"], capture_output=True, text=True, timeout=1
            )
            ui_updater.add_text_to_output(
                f"  ✅ subprocess.run worked: {result.stdout.strip()}\n"
            )
        except Exception as e:
            ui_updater.add_text_to_output(f"  ❌ subprocess.run failed: {e}\n")
    except Exception as e:
        ui_updater.add_text_to_output(f"  ❌ subprocess import failed: {e}\n")

    ui_updater.add_text_to_output("\nSignal handling test completed\n")

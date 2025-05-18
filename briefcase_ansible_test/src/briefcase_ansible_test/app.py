"""
A simple app to run ansible-inventory and display the results
"""

import os
import toga
from toga.style import Pack
import subprocess
import threading
import asyncio

# Define direction constants since they may not be available in the current Toga version
COLUMN = "column"
ROW = "row"


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application."""
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()

        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Title
        title_label = toga.Label(
            'Ansible Inventory Viewer',
            style=Pack(text_align='center', font_size=16, margin=5)
        )

        # Button to run ansible-inventory
        run_button = toga.Button(
            'Run ansible-inventory',
            on_press=self.run_ansible_inventory,
            style=Pack(margin=5)
        )

        # Output area
        self.output_view = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, margin=5)
        )

        # Status label
        self.status_label = toga.Label(
            'Ready',
            style=Pack(margin=5)
        )

        # Add components to main box
        main_box.add(title_label)
        main_box.add(run_button)
        main_box.add(self.output_view)
        main_box.add(self.status_label)

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

    def run_ansible_inventory(self, widget):
        """Run ansible-inventory command and display results."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Running ansible-inventory..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Path to ansible-inventory binary
                inventory_bin = os.path.join(self.paths.app, 'app_packages', 'bin', 'ansible-inventory')

                # Run with no parameters
                cmd = [inventory_bin]

                # Execute the command and capture output
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                # Prepare output text
                if process.returncode == 0:
                    output = f"Command: {inventory_bin}\n\n"
                    output += process.stdout
                    status = "Completed"
                else:
                    output = f"Command: {inventory_bin}\n\n"
                    output += f"Error (return code {process.returncode}):\n"
                    output += process.stderr
                    status = "Failed"

                # Update UI with results
                async def update_ui():
                    self.output_view.value = output
                    self.status_label.text = status

                # Create task and store reference to prevent garbage collection
                task = asyncio.create_task(update_ui())
                self.background_tasks.add(task)
                # Remove task from set when done
                task.add_done_callback(self.background_tasks.discard)

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)

                async def update_error():
                    self.output_view.value = f"Error: {error_message}"
                    self.status_label.text = "Error"

                # Create task and store reference to prevent garbage collection
                task = asyncio.create_task(update_error())
                self.background_tasks.add(task)
                # Remove task from set when done
                task.add_done_callback(self.background_tasks.discard)

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()


def main():
    app = briefcase_ansible_test()
    return app.main_loop()

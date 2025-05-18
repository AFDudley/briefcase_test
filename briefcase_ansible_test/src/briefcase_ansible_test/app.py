"""
A test to get ansible running in briefcase
"""

import os
import toga
from toga.style import Pack
import ansible_runner

# Define direction constants since they may not be available in the current Toga version
COLUMN = "column"
ROW = "row"


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application with Ansible functionality."""
        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Always assume mobile for iOS
        is_mobile = True

        # Set paths to look for resources
        self.playbooks_dir = os.path.join(self.paths.app, 'resources', 'playbooks')
        self.inventory_dir = os.path.join(self.paths.app, 'resources', 'inventory')

        # Create a combined display for file contents
        files_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        files_box.add(toga.Label('Files:', style=Pack(margin=(0, 5))))
        self.combined_content = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, width=350, height=180))
        files_box.add(self.combined_content)

        # Initialize these for compatibility with the load_file_contents method
        self.playbook_content = toga.MultilineTextInput(readonly=True)
        self.inventory_content = toga.MultilineTextInput(readonly=True)

        # Store file paths for later use
        self.playbook_path, self.inventory_path = self.get_sample_files()

        # Load and display file contents
        self.load_file_contents()

        # Run button
        run_button = toga.Button('Run Playbook', on_press=self.run_playbook, style=Pack(margin=10))

        # Status and output
        self.status_label = toga.Label('Ready', style=Pack(margin=5))
        self.output_view = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, margin=5, height=200))

        # Set up the main window first to allow proper size detection
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Add components to main box
        main_box.add(toga.Label('Ansible Runner', style=Pack(text_align='center', font_size=16, margin=5)))
        main_box.add(files_box)
        main_box.add(run_button)
        main_box.add(self.status_label)
        main_box.add(self.output_view)

        # Apply content and show window
        self.main_window.content = main_box

        # Set a maximum size for mobile
        if is_mobile:
            # Set explicit size to fit in iOS simulator viewport
            self.main_window.size = (380, 600)

        self.main_window.show()

    def get_sample_files(self):
        """Get paths to sample playbook and inventory files"""
        # Sample playbook path
        sample_playbook_path = os.path.join(self.playbooks_dir, 'sample_playbook.yml')
        # Sample inventory path
        sample_inventory_path = os.path.join(self.inventory_dir, 'sample_inventory.ini')

        return sample_playbook_path, sample_inventory_path

    def load_file_contents(self):
        """Load and display the contents of the sample files"""
        try:
            combined_content = "=== PLAYBOOK ===\n"

            # Load playbook content
            if os.path.exists(self.playbook_path):
                with open(self.playbook_path, 'r') as f:
                    playbook_content = f.read()
                self.playbook_content.value = playbook_content
                combined_content += playbook_content + "\n\n"
            else:
                self.playbook_content.value = "Sample playbook not found.\nExpected at: " + self.playbook_path
                combined_content += "Sample playbook not found.\n\n"

            combined_content += "=== INVENTORY ===\n"

            # Load inventory content
            if os.path.exists(self.inventory_path):
                with open(self.inventory_path, 'r') as f:
                    inventory_content = f.read()
                self.inventory_content.value = inventory_content
                combined_content += inventory_content
            else:
                self.inventory_content.value = "Sample inventory not found.\nExpected at: " + self.inventory_path
                combined_content += "Sample inventory not found."

            # Update the combined view
            self.combined_content.value = combined_content

        except Exception as exception:
            self.status_label.text = f"Error loading files: {str(exception)}"

    def run_playbook(self, widget):
        """Run the specified Ansible playbook"""
        # Reset the output display
        self.output_view.value = ""
        self.status_label.text = "Running playbook..."

        playbook = self.playbook_path
        inventory = self.inventory_path

        # Run in a background thread to keep the UI responsive
        def run_in_background():
            try:
                r = ansible_runner.run(
                    playbook=playbook,
                    inventory=inventory if inventory else None,
                    quiet=False,
                    json_mode=True
                )
                output = f"Playbook completed with status: {r.status}\n"
                output += f"Final return code: {r.rc}\n\n"

                # Update UI in the main thread
                def update_ui():
                    self.output_view.value = output
                    self.status_label.text = "Completed" if r.rc == 0 else "Failed"

                self.add_background_task(update_ui)

            except Exception as exception:
                # Capture the exception message outside the nested function
                error_message = str(exception)

                def update_error():
                    self.output_view.value = f"Error: {error_message}"
                    self.status_label.text = "Error"

                self.add_background_task(update_error)

        self.add_background_task(run_in_background)

def main():
    return briefcase_ansible_test()

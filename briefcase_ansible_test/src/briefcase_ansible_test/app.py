"""
A test to get ansible running in briefcase
"""

import os
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application with Ansible functionality."""
        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        # Always assume mobile for iOS
        is_mobile = True
        
        # Create playbook section
        if is_mobile:
            # Vertical layout for mobile
            playbook_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
            playbook_box.add(toga.Label('Playbook:', style=Pack(margin=(0, 5))))
            self.playbook_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=300))
            file_box = toga.Box(style=Pack(direction=ROW))
            file_box.add(self.playbook_path)
            playbook_button = toga.Button('...', on_press=self.select_playbook, style=Pack(width=40))
            file_box.add(playbook_button)
            playbook_box.add(file_box)
        else:
            # Horizontal layout for desktop
            playbook_box = toga.Box(style=Pack(direction=ROW, margin=5))
            playbook_box.add(toga.Label('Playbook:', style=Pack(margin=(0, 5), width=70)))
            self.playbook_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=250))
            playbook_box.add(self.playbook_path)
            playbook_button = toga.Button('Browse...', on_press=self.select_playbook)
            playbook_box.add(playbook_button)
        
        # Create inventory section
        if is_mobile:
            # Vertical layout for mobile
            inventory_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
            inventory_box.add(toga.Label('Inventory:', style=Pack(margin=(0, 5))))
            self.inventory_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=300))
            file_box = toga.Box(style=Pack(direction=ROW))
            file_box.add(self.inventory_path)
            inventory_button = toga.Button('...', on_press=self.select_inventory, style=Pack(width=40))
            file_box.add(inventory_button)
            inventory_box.add(file_box)
        else:
            # Horizontal layout for desktop
            inventory_box = toga.Box(style=Pack(direction=ROW, margin=5))
            inventory_box.add(toga.Label('Inventory:', style=Pack(margin=(0, 5), width=70)))
            self.inventory_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=250))
            inventory_box.add(self.inventory_path)
            inventory_button = toga.Button('Browse...', on_press=self.select_inventory)
            inventory_box.add(inventory_button)
        
        # Create default playbooks directory
        self.playbooks_dir = os.path.join(self.paths.app, 'playbooks')
        self.inventory_dir = os.path.join(self.paths.app, 'inventory')
        
        # Create directories if they don't exist
        os.makedirs(self.playbooks_dir, exist_ok=True)
        os.makedirs(self.inventory_dir, exist_ok=True)
        
        # Create a sample playbook and inventory if they don't exist
        self.create_sample_files()
        
        # Run button (smaller on mobile)
        if is_mobile:
            run_button = toga.Button('Run', on_press=self.run_playbook, style=Pack(margin=5))
        else:
            run_button = toga.Button('Run Playbook', on_press=self.run_playbook, style=Pack(margin=5))
        
        # Status and output
        self.status_label = toga.Label('Ready', style=Pack(margin=5))
        self.output_view = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, margin=5, height=200))
        
        # Set up the main window first to allow proper size detection
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Add components to main box - adjust based on mobile vs desktop
        title = 'Ansible' if is_mobile else 'Ansible Runner'
        main_box.add(toga.Label(title, style=Pack(text_align='center', font_size=16 if is_mobile else 18, margin=5)))
        main_box.add(playbook_box)
        main_box.add(inventory_box)
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
    
    def create_sample_files(self):
        """Create sample playbook and inventory files"""
        # Sample playbook
        sample_playbook_path = os.path.join(self.playbooks_dir, 'sample_playbook.yml')
        if not os.path.exists(sample_playbook_path):
            with open(sample_playbook_path, 'w') as f:
                f.write("""---
- name: Sample Playbook
  hosts: all
  gather_facts: false
  tasks:
    - name: Hello World
      debug:
        msg: "Hello from Ansible in Briefcase!"
""")
        
        # Sample inventory
        sample_inventory_path = os.path.join(self.inventory_dir, 'sample_inventory.ini')
        if not os.path.exists(sample_inventory_path):
            with open(sample_inventory_path, 'w') as f:
                f.write("""[local]
localhost ansible_connection=local
""")
    
    def select_playbook(self, widget):
        """Select a playbook file"""
        try:
            # For iOS, use a selection instead of a file dialog
            playbook_files = self.find_playbook_files()
            
            if not playbook_files:
                self.status_label.text = "No playbook files found"
                return
                
            # Create selection dialog with playbook files
            items = playbook_files
            selection = toga.Selection(items=items, on_select=self.on_playbook_selected)
            
            # Create a dialog to show the selection
            dialog_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
            dialog_box.add(toga.Label("Select Playbook:", style=Pack(margin=5)))
            dialog_box.add(selection)
            
            # Add a button to close the dialog
            button_box = toga.Box(style=Pack(direction=ROW, margin=5))
            cancel_button = toga.Button(
                "Cancel", 
                on_press=lambda w: self.close_selection_dialog(),
                style=Pack(flex=1, margin=5)
            )
            select_button = toga.Button(
                "Select", 
                on_press=lambda w: self.handle_playbook_selection(selection.value),
                style=Pack(flex=1, margin=5)
            )
            button_box.add(cancel_button)
            button_box.add(select_button)
            dialog_box.add(button_box)
            
            # Show as a new window
            self.selection_window = toga.Window(title="Select Playbook", size=(350, 300))
            self.selection_window.content = dialog_box
            self.selection_window.show()
            
        except Exception as e:
            self.status_label.text = f"Error selecting playbook: {str(e)}"
    
    def find_playbook_files(self):
        """Find all playbook files in the playbooks directory"""
        files = []
        if os.path.exists(self.playbooks_dir):
            for file in os.listdir(self.playbooks_dir):
                if file.endswith('.yml') or file.endswith('.yaml'):
                    files.append(file)
        return files
    
    def find_inventory_files(self):
        """Find all inventory files in the inventory directory"""
        files = []
        if os.path.exists(self.inventory_dir):
            for file in os.listdir(self.inventory_dir):
                if file.endswith('.ini'):
                    files.append(file)
        return files
    
    def close_selection_dialog(self):
        """Close the selection dialog window"""
        if hasattr(self, 'selection_window') and self.selection_window:
            self.selection_window.close()
    
    def handle_playbook_selection(self, filename):
        """Handle playbook selection from dialog"""
        if filename:
            full_path = os.path.join(self.playbooks_dir, filename)
            self.playbook_path.value = full_path
        self.close_selection_dialog()
    
    def on_playbook_selected(self, selection):
        """Handle selection of playbook from dropdown"""
        if selection.value:
            full_path = os.path.join(self.playbooks_dir, selection.value)
            self.playbook_path.value = full_path
    
    def select_inventory(self, widget):
        """Select an inventory file"""
        try:
            # For iOS, use a selection instead of a file dialog
            inventory_files = self.find_inventory_files()
            
            if not inventory_files:
                self.status_label.text = "No inventory files found"
                return
                
            # Create selection dialog with inventory files
            items = inventory_files
            selection = toga.Selection(items=items, on_select=self.on_inventory_selected)
            
            # Create a dialog to show the selection
            dialog_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
            dialog_box.add(toga.Label("Select Inventory:", style=Pack(margin=5)))
            dialog_box.add(selection)
            
            # Add a button to close the dialog
            button_box = toga.Box(style=Pack(direction=ROW, margin=5))
            cancel_button = toga.Button(
                "Cancel", 
                on_press=lambda w: self.close_inventory_dialog(),
                style=Pack(flex=1, margin=5)
            )
            select_button = toga.Button(
                "Select", 
                on_press=lambda w: self.handle_inventory_selection(selection.value),
                style=Pack(flex=1, margin=5)
            )
            button_box.add(cancel_button)
            button_box.add(select_button)
            dialog_box.add(button_box)
            
            # Show as a new window
            self.inventory_window = toga.Window(title="Select Inventory", size=(350, 300))
            self.inventory_window.content = dialog_box
            self.inventory_window.show()
            
        except Exception as e:
            self.status_label.text = f"Error selecting inventory: {str(e)}"
    
    def close_inventory_dialog(self):
        """Close the inventory selection dialog window"""
        if hasattr(self, 'inventory_window') and self.inventory_window:
            self.inventory_window.close()
    
    def handle_inventory_selection(self, filename):
        """Handle inventory selection from dialog"""
        if filename:
            full_path = os.path.join(self.inventory_dir, filename)
            self.inventory_path.value = full_path
        self.close_inventory_dialog()
    
    def on_inventory_selected(self, selection):
        """Handle selection of inventory from dropdown"""
        if selection.value:
            full_path = os.path.join(self.inventory_dir, selection.value)
            self.inventory_path.value = full_path
    
    def run_playbook(self, widget):
        """Run the specified Ansible playbook"""
        # Reset the output display
        self.output_view.value = ""
        self.status_label.text = "Running playbook..."
        
        try:
            playbook = self.playbook_path.value
            inventory = self.inventory_path.value
            
            if not playbook:
                self.status_label.text = "Error: Please select a playbook"
                return
                
            # Import ansible_runner here to avoid startup delays
            # and potential issues on platforms where it might not be available
            import ansible_runner
            
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
                    
                    # Show event output
                    if r.events:
                        output += "Events:\n"
                        for event in r.events:
                            if event['event'] == 'runner_on_ok':
                                task_name = event.get('event_data', {}).get('task', '')
                                host = event.get('event_data', {}).get('host', '')
                                if 'res' in event.get('event_data', {}):
                                    if 'msg' in event['event_data']['res']:
                                        msg = event['event_data']['res']['msg']
                                        output += f"✓ {host}: {task_name} - {msg}\n"
                                    else:
                                        output += f"✓ {host}: {task_name}\n"
                            elif event['event'] == 'runner_on_failed':
                                task_name = event.get('event_data', {}).get('task', '')
                                host = event.get('event_data', {}).get('host', '')
                                output += f"✗ {host}: {task_name} - FAILED\n"
                    
                    # Update UI in the main thread
                    def update_ui():
                        self.output_view.value = output
                        self.status_label.text = "Completed" if r.rc == 0 else "Failed"
                    
                    self.add_background_task(update_ui)
                    
                except Exception as e:
                    def update_error():
                        self.output_view.value = f"Error: {str(e)}"
                        self.status_label.text = "Error"
                    
                    self.add_background_task(update_error)
            
            self.add_background_task(run_in_background)
            
        except ImportError:
            self.output_view.value = (
                "Error: ansible_runner module not available.\n"
                "This may not be supported on your current platform."
            )
            self.status_label.text = "Error: Missing dependencies"
        except Exception as e:
            self.output_view.value = f"Error: {str(e)}"
            self.status_label.text = "Error"


def main():
    return briefcase_ansible_test()

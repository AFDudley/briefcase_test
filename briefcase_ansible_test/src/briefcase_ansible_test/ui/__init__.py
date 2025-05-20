"""
UI Components for the Briefcase Ansible Test application.
"""

import threading
import asyncio


class UIComponents:
    """Utility class for working with UI components."""
    
    @staticmethod
    def create_output_area(app):
        """Create and return the output text area and status label."""
        from toga.style import Pack
        import toga
        
        # Output text area for displaying results
        output_view = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, margin=5)
        )

        # Status label for showing current state
        status_label = toga.Label(
            'Ready',
            style=Pack(margin=5)
        )

        return output_view, status_label
    
    @staticmethod
    def create_main_layout(app, action_buttons, output_view, status_label):
        """Create and return the main layout with all UI components."""
        from toga.style import Pack
        import toga
        
        # Main box with vertical layout
        main_box = toga.Box(style=Pack(direction="column", margin=10))

        # App title
        title_label = toga.Label(
            'Ansible Inventory Viewer',
            style=Pack(text_align='center', font_size=16, margin=5)
        )

        # Add components to main box
        main_box.add(title_label)
        # Add all action buttons
        for button in action_buttons:
            main_box.add(button)
        main_box.add(output_view)
        main_box.add(status_label)

        return main_box


class UIUpdater:
    """Helper class for updating the UI from background threads."""
    
    def __init__(self, app):
        self.app = app
    
    def add_text_to_output(self, text):
        """Add text to the output view from any thread."""
        self.app.add_text_to_output(text)
    
    def update_status(self, text):
        """Update the status label from any thread."""
        self.app.update_status(text)


class BackgroundTaskRunner:
    """Helper class for running tasks in background threads."""
    
    def __init__(self, app):
        self.app = app
        self.background_tasks = self.app.background_tasks
    
    def run_task(self, task_func, initial_status="Working..."):
        """
        Execute a function in a background thread with proper error handling.
        
        Args:
            task_func: The function to execute in the background
            initial_status: The status message to display while task is running
        """
        # Clear output and update status
        self.app.output_view.value = ""
        self.app.status_label.text = initial_status
        
        # Create a wrapper function to handle exceptions
        def background_wrapper():
            try:
                # Execute the actual task
                task_func()
            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.app.add_text_to_output(f"Error: {error_message}")
                self.app.update_status("Error")
                # Add traceback for debugging
                import traceback
                self.app.add_text_to_output(f"\nTraceback:\n{traceback.format_exc()}")
        
        # Start background thread
        thread = threading.Thread(target=background_wrapper)
        thread.daemon = True
        thread.start()
        
        # Store the thread to prevent garbage collection
        self.background_tasks.add(thread)
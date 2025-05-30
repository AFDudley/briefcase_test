"""
UI components for briefcase_ansible_test
"""

import toga
from toga.style import Pack
import asyncio
import threading
import logging
from briefcase_ansible_test.utils.data_processing import categorize_log_level


class StatusReporter:
    """Standardized status reporting for consistent user feedback."""

    def __init__(self):
        """Initialize the status reporter with empty message lists."""
        self._success_messages = []
        self._error_messages = []
        self._warning_messages = []

    def success(self, message: str) -> str:
        """
        Record a success message.

        Args:
            message: The success message

        Returns:
            The formatted message
        """
        self._success_messages.append(message)
        return f"SUCCESS: {message}"

    def error(self, message: str) -> str:
        """
        Record an error message.

        Args:
            message: The error message

        Returns:
            The formatted message
        """
        self._error_messages.append(message)
        return f"ERROR: {message}"

    def warning(self, message: str) -> str:
        """
        Record a warning message.

        Args:
            message: The warning message

        Returns:
            The formatted message
        """
        self._warning_messages.append(message)
        return f"WARNING: {message}"

    def get_summary(self) -> str:
        """
        Get a summary of all recorded messages.

        Returns:
            A formatted summary string
        """
        parts = []

        if self._success_messages:
            parts.append(f"Successes ({len(self._success_messages)}):")
            for msg in self._success_messages:
                parts.append(f"  - {msg}")

        if self._warning_messages:
            parts.append(f"Warnings ({len(self._warning_messages)}):")
            for msg in self._warning_messages:
                parts.append(f"  - {msg}")

        if self._error_messages:
            parts.append(f"Errors ({len(self._error_messages)}):")
            for msg in self._error_messages:
                parts.append(f"  - {msg}")

        if not parts:
            return "No messages recorded"

        return "\n".join(parts)


class UIComponents:
    """Helper class for creating and managing UI components."""

    @staticmethod
    def create_output_area():
        """Create and return the output text area and status label."""
        # Output text area for displaying results
        output_view = toga.MultilineTextInput(
            readonly=True, style=Pack(flex=1, margin=5)
        )

        # Status label for showing current state
        status_label = toga.Label("Ready", style=Pack(margin=5))

        return output_view, status_label

    @staticmethod
    def create_action_buttons(app, button_configs):
        """Create and return action buttons for the application.

        Args:
            app: The app instance providing callback methods
            button_configs: Button configurations as list of tuples.
                           Each tuple should contain (label, callback, tooltip).

        Returns:
            A list of Toga Button widgets

        Raises:
            ValueError: If button_configs is None or empty
        """
        if not button_configs:
            raise ValueError("Button configurations must be provided")

        # Create buttons from configuration tuples
        return [
            toga.Button(label, on_press=callback, style=Pack(margin=5))
            for label, callback, _ in button_configs
        ]

    @staticmethod
    def create_main_layout(title, action_buttons, output_view, status_label):
        """Create and return the main layout with all UI components."""
        # Main box with vertical layout
        main_box = toga.Box(style=Pack(direction="column", margin=10))

        # App title
        title_label = toga.Label(
            title, style=Pack(text_align="center", font_size=16, margin=5)
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
    """Helper class for updating UI from background threads with automatic logging."""

    def __init__(self, output_view, status_label, main_event_loop, logger=None):
        """Initialize with UI components to update."""
        self.output_view = output_view
        self.status_label = status_label
        self.main_event_loop = main_event_loop
        self.logger = logger or logging.getLogger("UIUpdater")

    def add_text_to_output(self, text):
        """Add text to the output view from any thread and automatically log it."""
        # Automatically log all output text
        # Use pure function to determine log level
        text_clean = text.strip()
        log_level = categorize_log_level(text)

        if log_level == "ERROR":
            self.logger.error(f"UI OUTPUT: {text_clean}")
        elif log_level == "WARNING":
            self.logger.warning(f"UI OUTPUT: {text_clean}")
        else:
            self.logger.info(f"UI OUTPUT: {text_clean}")

        def update_ui():
            self.output_view.value += text

        # If we're on the main thread, update directly
        if threading.current_thread() is threading.main_thread():
            update_ui()
        else:
            # Create a direct coroutine for updating the text
            async def update_text():
                self.output_view.value += text

            # Schedule it on the main event loop
            asyncio.run_coroutine_threadsafe(update_text(), self.main_event_loop)

    def update_status(self, text):
        """Update the status label from any thread and log status changes."""
        self.logger.info(f"STATUS: {text}")

        def update_ui():
            self.status_label.text = text

        # If we're on the main thread, update directly
        if threading.current_thread() is threading.main_thread():
            update_ui()
        else:
            # Create a direct coroutine for updating the status
            async def update_status_text():
                self.status_label.text = text

            # Schedule it on the main event loop
            asyncio.run_coroutine_threadsafe(update_status_text(), self.main_event_loop)

    def clear_output(self):
        """Clear the output area."""

        def update_ui():
            self.output_view.value = ""

        # If we're on the main thread, update directly
        if threading.current_thread() is threading.main_thread():
            update_ui()
        else:
            # Create a direct coroutine for clearing
            async def clear_text():
                self.output_view.value = ""

            # Schedule it on the main event loop
            asyncio.run_coroutine_threadsafe(clear_text(), self.main_event_loop)


class BackgroundTaskRunner:
    """Helper class for running tasks in background threads."""

    def __init__(self, ui_updater):
        """Initialize with a UI updater for communicating results."""
        self.ui_updater = ui_updater
        self.background_tasks = set()  # Keep references to prevent garbage collection

    def run_task(self, task_func, initial_status="Working..."):
        """
        Execute a function in a background thread with proper error handling.

        Args:
            task_func: The function to execute in the background
            initial_status: The status message to display while task is running
        """
        import traceback

        # Clear output and update status
        self.ui_updater.clear_output()
        self.ui_updater.update_status(initial_status)

        # Create a wrapper function to handle exceptions
        def background_wrapper():
            try:
                # Execute the actual task
                task_func()
                # Task completed successfully - clear the status
                self.ui_updater.update_status("Ready")
            except Exception as error:
                # Handle any exceptions - logging is automatic via UIUpdater
                error_message = str(error)
                traceback_str = traceback.format_exc()

                self.ui_updater.add_text_to_output(f"Error: {error_message}\n")
                self.ui_updater.add_text_to_output(f"Traceback:\n{traceback_str}\n")
                self.ui_updater.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=background_wrapper)
        thread.daemon = True
        thread.start()

        # Store the thread to prevent garbage collection
        self.background_tasks.add(thread)

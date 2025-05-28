"""
Logging utilities for briefcase_ansible_test
"""

import logging
import datetime
import os
import sys


def setup_app_logging(app_paths):
    """Set up global logging to file in the app's resource directory."""
    try:
        # Create logs directory in the app's resource folder
        logs_dir = os.path.join(app_paths.app, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"briefcase_ansible_test_{timestamp}.log")
        
        # Set up root logger to capture everything
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
        
        # Set up global exception handler
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        sys.excepthook = handle_exception
        
        return log_file
        
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        return None


class AppLogger:
    """Wrapper for app-specific logging functionality."""
    
    def __init__(self, logger_name="BriefcaseAnsibleTest"):
        self.logger = logging.getLogger(logger_name)
        if self.logger:
            self.logger.info(f"Logger initialized: {logger_name}")
    
    def log_error(self, message, exception=None):
        """Log an error message and optional exception."""
        if self.logger:
            if exception:
                self.logger.error(f"{message}: {exception}", exc_info=True)
            else:
                self.logger.error(message)
        else:
            print(f"LOG ERROR: {message}")
            if exception:
                print(f"EXCEPTION: {exception}")

    def log_info(self, message):
        """Log an info message."""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"LOG INFO: {message}")
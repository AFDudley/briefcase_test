"""
Mock implementation of the pwd module for iOS.

The pwd module is not available on iOS, but many Python libraries expect it to exist.
This mock provides the minimum functionality needed by Ansible and other libraries.
"""

import sys
import types


class PwdModule:
    """
    A mock implementation of the pwd module for platforms where it's not available.

    This provides the minimum functionality needed by Ansible and other libraries
    that expect the pwd module to be present.
    """

    class Struct:
        """
        A simple structure class that can be used to create objects with arbitrary attributes.
        """

        def __init__(self, **entries):
            """
            Initialize the structure with the given key-value pairs as attributes.

            Args:
                **entries: Arbitrary keyword arguments that will become attributes.
            """
            self.__dict__.update(entries)

    def getpwuid(self, uid):
        """
        Get a passwd struct by user ID.

        Args:
            uid: The user ID (ignored in this implementation).

        Returns:
            Struct: A struct with a pw_name attribute set to 'mobile'.
        """
        return self.Struct(pw_name="mobile")

    def getpwnam(self, name):
        """
        Get a passwd struct by username.

        Args:
            name: The username (ignored in this implementation).

        Returns:
            Struct: A struct with pw_uid, pw_gid, and pw_dir attributes.
        """
        return self.Struct(pw_uid=0, pw_gid=0, pw_dir="/home/mobile")


def setup_pwd_module_mock():
    """
    Install a mock pwd module in sys.modules if it doesn't already exist.

    This should be called before importing any modules that might depend on
    the pwd module, particularly on platforms where pwd is not available.
    """
    if "pwd" not in sys.modules:

        class PwdModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("pwd")
                self.getpwuid = PwdModule().getpwuid
                self.getpwnam = PwdModule().getpwnam

        sys.modules["pwd"] = PwdModuleType()

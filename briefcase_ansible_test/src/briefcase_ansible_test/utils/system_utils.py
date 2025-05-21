"""
System utility functions for cross-platform compatibility.

These utilities provide platform-independent implementations of system functions
that might not be available on all platforms (particularly iOS).
"""

import os
import sys
import stat
import getpass


def simple_getuser():
    """
    Cross-platform username getter that doesn't rely on the pwd module.

    This is especially useful on platforms like iOS where the pwd module
    is not available.

    Returns:
        str: The username from environment variables or 'mobile' if not found.
    """
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        user = os.environ.get(name)
        if user:
            return user
    return "mobile"  # Default iOS user


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
        import types

        class PwdModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("pwd")
                self.getpwuid = PwdModule().getpwuid
                self.getpwnam = PwdModule().getpwnam

        sys.modules["pwd"] = PwdModuleType()


def patch_getpass():
    """
    Replace getpass.getuser with our simple_getuser implementation.

    This should be called before any code that might use getpass.getuser.
    """
    getpass.getuser = simple_getuser


class GrpModule:
    """
    A mock implementation of the grp module for platforms where it's not available.

    This provides the minimum functionality needed by Ansible and other libraries
    that expect the grp module to be present.
    """

    class Struct:
        """
        A simple structure class that can be used to create objects with arbitrary attributes.
        """

        def __init__(self, **entries):
            """
            Initialize the structure with the given key-value pairs as attributes.
            """
            self.__dict__.update(entries)

    def getgrgid(self, gid):
        """
        Get a group struct by group ID.

        Args:
            gid: The group ID (ignored in this implementation).

        Returns:
            Struct: A struct with a gr_name attribute set to 'mobile'.
        """
        return self.Struct(gr_name="mobile")

    def getgrnam(self, name):
        """
        Get a group struct by group name.

        Args:
            name: The group name (ignored in this implementation).

        Returns:
            Struct: A struct with gr_gid attribute and empty gr_mem list.
        """
        return self.Struct(gr_gid=0, gr_mem=[])


def setup_grp_module_mock():
    """
    Install a mock grp module in sys.modules if it doesn't already exist.

    This should be called before importing any modules that might depend on
    the grp module, particularly on platforms where grp is not available.
    """
    if "grp" not in sys.modules:
        import types

        class GrpModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("grp")
                self.getgrgid = GrpModule().getgrgid
                self.getgrnam = GrpModule().getgrnam

        sys.modules["grp"] = GrpModuleType()

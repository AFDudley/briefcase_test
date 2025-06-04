"""
Mock implementation of the grp module for iOS.

The grp module is not available on iOS, but many Python libraries expect it to exist.
This mock provides the minimum functionality needed by Ansible and other libraries.
"""

import sys
import types


class GrpModule:
    """
    A mock implementation of the grp module for platforms where it's not available.

    This provides the minimum functionality needed by Ansible and other libraries
    that expect the grp module to be present.
    """

    class Struct:
        """
        A simple structure class that can be used to create objects with
        arbitrary attributes.
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

        class GrpModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("grp")
                self.getgrgid = GrpModule().getgrgid
                self.getgrnam = GrpModule().getgrnam

        sys.modules["grp"] = GrpModuleType()

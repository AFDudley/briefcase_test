"""
Ansible collections setup for iOS compatibility.

This module sets up the ansible_collections module hierarchy in sys.modules
since iOS doesn't have the filesystem structure that Ansible expects.
"""

import sys
import types


def setup_ansible_collections():
    """Set up ansible_collections module hierarchy in sys.modules"""
    if "ansible_collections" not in sys.modules:
        # Root module
        ansible_collections = types.ModuleType("ansible_collections")
        ansible_collections.__path__ = ["/mock/ansible_collections"]
        sys.modules["ansible_collections"] = ansible_collections
        
        # ansible namespace
        ansible_ns = types.ModuleType("ansible_collections.ansible")
        ansible_ns.__path__ = ["/mock/ansible_collections/ansible"]
        sys.modules["ansible_collections.ansible"] = ansible_ns
        setattr(ansible_collections, "ansible", ansible_ns)
        
        # builtin namespace
        builtin_ns = types.ModuleType("ansible_collections.ansible.builtin")
        builtin_ns.__path__ = ["/mock/ansible_collections/ansible/builtin"]
        sys.modules["ansible_collections.ansible.builtin"] = builtin_ns
        setattr(ansible_ns, "builtin", builtin_ns)
        
        # plugins namespace
        plugins_ns = types.ModuleType("ansible_collections.ansible.builtin.plugins")
        plugins_ns.__path__ = ["/mock/ansible_collections/ansible/builtin/plugins"]
        sys.modules["ansible_collections.ansible.builtin.plugins"] = plugins_ns
        setattr(builtin_ns, "plugins", plugins_ns)
        
        # modules namespace
        modules_ns = types.ModuleType("ansible_collections.ansible.builtin.plugins.modules")
        modules_ns.__path__ = ["/mock/ansible_collections/ansible/builtin/plugins/modules"]
        sys.modules["ansible_collections.ansible.builtin.plugins.modules"] = modules_ns
        setattr(plugins_ns, "modules", modules_ns)
        
        print("iOS_DEBUG: ansible_collections hierarchy created")
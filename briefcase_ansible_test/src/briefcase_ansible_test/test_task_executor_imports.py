"""
Test importing task_executor dependencies step by step
"""


def test_task_executor_imports(ui_updater):
    """Test task_executor imports step by step to find the hang"""
    ui_updater.add_text_to_output("Testing task_executor imports step by step...\n")

    # Test imports that task_executor uses
    imports_to_test = [
        ("ansible", "Base ansible module"),
        ("ansible.errors", "Ansible errors"),
        ("ansible.executor", "Executor module"),
        ("ansible.module_utils.common.text.converters", "Text converters"),
        ("ansible.module_utils._text", "Text utilities"),
        ("ansible.parsing.utils.jsonify", "JSON utilities"),
        ("ansible.plugins", "Plugins module"),
        ("ansible.plugins.loader", "Plugin loader"),
        ("ansible.template", "Template module"),
        ("ansible.utils.context_objects", "Context objects"),
        ("ansible.utils.display", "Display module"),
        ("ansible.utils.unsafe_proxy", "Unsafe proxy"),
        ("ansible.utils.vars", "Variable utilities"),
        ("ansible.vars.clean", "Variable cleaning"),
    ]

    for module_name, description in imports_to_test:
        ui_updater.add_text_to_output(f"\nTrying {module_name} ({description})... ")
        try:
            module = __import__(module_name, fromlist=[""])
            ui_updater.add_text_to_output(f"✅")
        except Exception as e:
            ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Now try specific imports from task_executor
    ui_updater.add_text_to_output(
        "\n\nTesting specific imports from task_executor file...\n"
    )

    # Test action loader specifically
    ui_updater.add_text_to_output("\nTrying to import action_loader... ")
    try:
        from ansible.plugins.loader import action_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test connection loader
    ui_updater.add_text_to_output("\nTrying to import connection_loader... ")
    try:
        from ansible.plugins.loader import connection_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test filter loader
    ui_updater.add_text_to_output("\nTrying to import filter_loader... ")
    try:
        from ansible.plugins.loader import filter_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test test loader
    ui_updater.add_text_to_output("\nTrying to import test_loader... ")
    try:
        from ansible.plugins.loader import test_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test lookup loader
    ui_updater.add_text_to_output("\nTrying to import lookup_loader... ")
    try:
        from ansible.plugins.loader import lookup_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test module loader
    ui_updater.add_text_to_output("\nTrying to import module_loader... ")
    try:
        from ansible.plugins.loader import module_loader

        ui_updater.add_text_to_output("✅")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    # Test constants access
    ui_updater.add_text_to_output("\n\nTesting ansible constants access...\n")

    ui_updater.add_text_to_output("Trying to import ansible constants... ")
    try:
        from ansible import constants as C

        ui_updater.add_text_to_output("✅")

        ui_updater.add_text_to_output("\nTrying to access C.MAGIC_VARIABLE_MAPPING... ")
        mapping = C.MAGIC_VARIABLE_MAPPING
        ui_updater.add_text_to_output(f"✅ Type: {type(mapping)}")

        ui_updater.add_text_to_output(
            "\nTrying to access C.MAGIC_VARIABLE_MAPPING.items()... "
        )
        items = mapping.items()
        ui_updater.add_text_to_output(f"✅ Got {len(list(items))} items")

        ui_updater.add_text_to_output("\nTrying RETURN_VARS creation... ")
        RETURN_VARS = [
            x
            for x in C.MAGIC_VARIABLE_MAPPING.items()
            if "become" not in x and "_pass" not in x
        ]
        ui_updater.add_text_to_output(f"✅ Created {len(RETURN_VARS)} RETURN_VARS")

    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")
        import traceback

        ui_updater.add_text_to_output(f"\nTraceback: {traceback.format_exc()}")

    # Test creating Display instance at module level
    ui_updater.add_text_to_output(
        "\n\nTesting Display instantiation at module level...\n"
    )
    try:
        ui_updater.add_text_to_output("Importing Display... ")
        from ansible.utils.display import Display

        ui_updater.add_text_to_output("✅")

        ui_updater.add_text_to_output("\nCreating Display instance... ")
        display = Display()
        ui_updater.add_text_to_output(f"✅ {display}")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ {type(e).__name__}: {e}")

    ui_updater.add_text_to_output("\n\nTask executor import test completed\n")

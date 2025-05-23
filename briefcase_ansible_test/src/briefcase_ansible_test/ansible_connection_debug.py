"""
Debug Ansible connection plugins to see what's failing
"""


def patch_connection_plugins():
    """Patch connection plugins to add debugging"""
    try:
        # Import after Ansible is loaded
        from ansible.plugins.loader import connection_loader

        # Get the local connection plugin
        local_connection = connection_loader.get("local")
        print(f"iOS_DEBUG: connection_loader.get('local') returned: {local_connection}")
        if local_connection:
            print(f"iOS_DEBUG: Found local connection plugin: {local_connection}")

            # Patch the put_file method if it exists
            if hasattr(local_connection, "put_file"):
                original_put_file = local_connection.put_file

                def debug_put_file(self, in_path, out_path):
                    print(f"iOS_DEBUG: put_file called: {in_path} -> {out_path}")

                    # Redirect /home/mobile paths to iOS writable directory
                    import tempfile
                    import os

                    if "/home/mobile" in out_path:
                        ios_writable_dir = tempfile.gettempdir()
                        redirected_path = out_path.replace(
                            "/home/mobile", ios_writable_dir
                        )
                        print(
                            f"iOS_DEBUG: Redirecting path: {out_path} -> {redirected_path}"
                        )
                        out_path = redirected_path

                    # Make sure the directory exists
                    out_dir = os.path.dirname(out_path)
                    if not os.path.exists(out_dir):
                        print(f"iOS_DEBUG: Creating directory: {out_dir}")
                        try:
                            os.makedirs(out_dir, exist_ok=True)
                        except Exception as e:
                            print(
                                f"iOS_DEBUG: Failed to create directory {out_dir}: {e}"
                            )

                    try:
                        result = original_put_file(self, in_path, out_path)
                        print(f"iOS_DEBUG: put_file succeeded")
                        return result
                    except Exception as e:
                        print(f"iOS_DEBUG: put_file failed: {e}")

                        # Try to create the file manually as a fallback
                        try:
                            import shutil

                            shutil.copy2(in_path, out_path)
                            print(f"iOS_DEBUG: Manual copy succeeded")
                        except Exception as e2:
                            print(f"iOS_DEBUG: Manual copy also failed: {e2}")
                            raise e

                local_connection.put_file = debug_put_file
                print("iOS_DEBUG: Patched local connection put_file method")

            return True
        else:
            print("iOS_DEBUG: Could not find local connection plugin")
            return False

    except Exception as e:
        print(f"iOS_DEBUG: Failed to patch connection plugins: {e}")
        return False

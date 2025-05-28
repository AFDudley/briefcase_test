"""
Mock CompletedProcess for subprocess compatibility.
"""


class MockCompletedProcess:
    """Mock implementation of subprocess.CompletedProcess."""

    def __init__(self, args, returncode=0, stdout=b"", stderr=b""):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

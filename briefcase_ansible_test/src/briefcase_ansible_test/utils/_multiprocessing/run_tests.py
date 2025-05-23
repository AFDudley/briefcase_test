#!/usr/bin/env python3
"""
Test runner for iOS multiprocessing implementation.

Usage:
    python run_tests.py               # Run all tests
    python run_tests.py unit          # Run only unit tests
    python run_tests.py integration   # Run only integration tests
    python run_tests.py system        # Run only system tests
    python run_tests.py --verbose     # Run with verbose output
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type=None, verbose=False):
    """Run the test suite."""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test path
    test_dir = Path(__file__).parent / "tests"

    if test_type == "unit":
        cmd.extend([str(test_dir), "-m", "unit"])
    elif test_type == "integration":
        cmd.extend([str(test_dir), "-m", "integration"])
    elif test_type == "system":
        cmd.extend([str(test_dir), "-m", "system"])
    else:
        cmd.append(str(test_dir))

    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")

    # Add additional useful flags
    cmd.extend(
        [
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker checking
        ]
    )

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run iOS multiprocessing tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["unit", "integration", "system"],
        help="Type of tests to run (default: all)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("🧪 iOS Threading-Based Multiprocessing Test Runner")
    print("=" * 60)

    if args.test_type:
        print(f"Running {args.test_type} tests...")
    else:
        print("Running all tests...")

    return run_tests(args.test_type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test runner script for nexios-contrib.

This script provides convenient commands to run tests for the nexios-contrib package.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: str, **kwargs):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    return subprocess.run(cmd.split(), **kwargs)


def run_tests(args: str = ""):
    """Run pytest with the given arguments."""
    cmd = f"python -m pytest {args}"
    return run_command(cmd, cwd=Path(__file__).parent)


def run_unit_tests():
    """Run only unit tests."""
    return run_tests("tests/ -m unit -v")


def run_integration_tests():
    """Run only integration tests."""
    return run_tests("tests/integration/ -m integration -v")


def run_redis_tests():
    """Run only Redis-related tests."""
    return run_tests("tests/redis/ -v")


def run_accepts_tests():
    """Run only Accepts-related tests."""
    return run_tests("tests/accepts/ -v")


def run_etag_tests():
    """Run only ETag-related tests."""
    return run_tests("tests/etag/ -v")


def run_all_tests():
    """Run all tests."""
    return run_tests("tests/ -v")


def run_coverage():
    """Run tests with coverage."""
    return run_tests("tests/ --cov=nexios_contrib --cov-report=html --cov-report=term")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [command]")
        print("Commands:")
        print("  unit        - Run unit tests")
        print("  integration - Run integration tests")
        print("  redis       - Run Redis tests")
        print("  accepts     - Run Accepts tests")
        print("  etag        - Run ETag tests")
        print("  coverage    - Run tests with coverage")
        print("  all         - Run all tests (default)")
        return 1

    command = sys.argv[1]

    commands = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "redis": run_redis_tests,
        "accepts": run_accepts_tests,
        "etag": run_etag_tests,
        "coverage": run_coverage,
        "all": run_all_tests,
    }

    if command in commands:
        return commands[command]()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

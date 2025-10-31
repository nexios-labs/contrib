#!/usr/bin/env python3
"""
Redis integration test runner.

This script provides different ways to run Redis tests:
1. Unit tests with mocked Redis (default)
2. Integration tests with real Redis server
3. All tests including performance benchmarks
"""
import sys
import subprocess
import argparse
from pathlib import Path


def check_redis_available():
    """Check if Redis server is available."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return True
    except (ImportError, redis.ConnectionError, redis.TimeoutError):
        return False


def run_unit_tests():
    """Run unit tests with mocked Redis."""
    print("Running Redis unit tests with mocked Redis...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_redis/",
        "-v",
        "--tb=short",
        "-m", "not integration",
        "--cov=nexios_contrib.redis",
        "--cov-report=term-missing"
    ]
    return subprocess.run(cmd).returncode


def run_integration_tests():
    """Run integration tests with real Redis."""
    if not check_redis_available():
        print("❌ Redis server not available. Please start Redis server first.")
        print("   docker run -d -p 6379:6379 redis:latest")
        return 1
    
    print("Running Redis integration tests with real Redis server...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_redis/test_redis_real_integration.py",
        "-v",
        "--tb=short",
        "-m", "integration"
    ]
    return subprocess.run(cmd).returncode


def run_all_tests():
    """Run all Redis tests."""
    print("Running all Redis tests...")
    
    # Run unit tests first
    unit_result = run_unit_tests()
    if unit_result != 0:
        print("❌ Unit tests failed")
        return unit_result
    
    print("✅ Unit tests passed")
    
    # Run integration tests if Redis is available
    if check_redis_available():
        print("\n" + "="*50)
        integration_result = run_integration_tests()
        if integration_result != 0:
            print("❌ Integration tests failed")
            return integration_result
        print("✅ Integration tests passed")
    else:
        print("⚠️  Skipping integration tests (Redis not available)")
    
    return 0


def run_specific_test(test_file):
    """Run a specific test file."""
    print(f"Running specific test: {test_file}")
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/test_redis/{test_file}",
        "-v",
        "--tb=short"
    ]
    return subprocess.run(cmd).returncode


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Redis integration test runner")
    parser.add_argument(
        "--mode",
        choices=["unit", "integration", "all"],
        default="unit",
        help="Test mode to run (default: unit)"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file (e.g., test_redis_client.py)"
    )
    parser.add_argument(
        "--setup-redis",
        action="store_true",
        help="Show Redis setup instructions"
    )
    
    args = parser.parse_args()
    
    if args.setup_redis:
        print("Redis Setup Instructions:")
        print("========================")
        print("1. Using Docker:")
        print("   docker run -d -p 6379:6379 --name redis-test redis:latest")
        print("")
        print("2. Using local installation:")
        print("   # On macOS with Homebrew:")
        print("   brew install redis")
        print("   brew services start redis")
        print("")
        print("   # On Ubuntu/Debian:")
        print("   sudo apt-get install redis-server")
        print("   sudo systemctl start redis-server")
        print("")
        print("3. Verify Redis is running:")
        print("   redis-cli ping")
        print("   # Should return: PONG")
        return 0
    
    if args.file:
        return run_specific_test(args.file)
    
    if args.mode == "unit":
        return run_unit_tests()
    elif args.mode == "integration":
        return run_integration_tests()
    elif args.mode == "all":
        return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
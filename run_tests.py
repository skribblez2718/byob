#!/usr/bin/env python3
"""
Test runner script for the Flask blog application.
Provides convenient commands to run different types of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests for Flask blog application")
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "integration", "models", "repositories", "services", "routes", "utils", "coverage"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage report"
    )
    parser.add_argument(
        "--html-coverage",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.coverage or args.test_type == "coverage":
        base_cmd.extend(["--cov=app", "--cov-report=term-missing"])
        if args.html_coverage:
            base_cmd.append("--cov-report=html:htmlcov")
    
    # Test type specific commands
    test_commands = {
        "all": base_cmd + ["tests/"],
        "unit": base_cmd + ["tests/test_models.py", "tests/test_repositories.py", "tests/test_services.py", "tests/test_utils.py"],
        "integration": base_cmd + ["tests/test_integration.py"],
        "models": base_cmd + ["tests/test_models.py"],
        "repositories": base_cmd + ["tests/test_repositories.py"],
        "services": base_cmd + ["tests/test_services.py"],
        "routes": base_cmd + ["tests/test_routes.py"],
        "utils": base_cmd + ["tests/test_utils.py"],
        "coverage": base_cmd + ["tests/", "--cov=app", "--cov-report=term-missing", "--cov-report=html:htmlcov"]
    }
    
    cmd = test_commands[args.test_type]
    description = f"{args.test_type.title()} tests"
    
    exit_code = run_command(cmd, description)
    
    if exit_code == 0:
        print(f"\n✅ {description} completed successfully!")
        if args.test_type == "coverage" or args.html_coverage:
            print("📊 HTML coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ {description} failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

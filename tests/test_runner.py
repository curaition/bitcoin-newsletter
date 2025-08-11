"""Test runner script for the crypto newsletter test suite."""

import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def run_tests(
    test_type: Optional[str] = None,
    coverage: bool = True,
    verbose: bool = False,
    parallel: bool = False,
    specific_test: Optional[str] = None,
    markers: Optional[str] = None
) -> int:
    """
    Run the test suite with various options.
    
    Args:
        test_type: Type of tests to run ('unit', 'integration', 'all')
        coverage: Whether to generate coverage reports
        verbose: Whether to run in verbose mode
        parallel: Whether to run tests in parallel
        specific_test: Specific test file or function to run
        markers: Pytest markers to filter tests
        
    Returns:
        Exit code from pytest
    """
    cmd = ["python", "-m", "pytest"]
    
    # Add test path based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif specific_test:
        cmd.append(specific_test)
    else:
        cmd.append("tests/")
    
    # Add markers
    if markers:
        cmd.extend(["-m", markers])
    elif test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    
    # Add coverage options
    if coverage:
        cmd.extend([
            "--cov=src/crypto_newsletter",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("Warning: pytest-xdist not installed, running tests sequentially")
    
    # Add other useful options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
        "--strict-config",  # Strict config checking
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def run_linting() -> int:
    """Run code linting checks."""
    print("Running linting checks...")
    
    commands = [
        ["python", "-m", "black", "--check", "src/", "tests/"],
        ["python", "-m", "ruff", "check", "src/", "tests/"],
        ["python", "-m", "mypy", "src/"]
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            return result.returncode
    
    return 0


def run_security_checks() -> int:
    """Run security checks."""
    print("Running security checks...")
    
    try:
        # Check if bandit is available
        result = subprocess.run(
            ["python", "-m", "bandit", "-r", "src/", "-f", "json"],
            capture_output=True
        )
        if result.returncode != 0:
            print("Security issues found by bandit")
            print(result.stdout.decode())
            return result.returncode
    except FileNotFoundError:
        print("Bandit not installed, skipping security checks")
    
    return 0


def generate_test_report() -> None:
    """Generate a comprehensive test report."""
    print("Generating test report...")
    
    # Run all tests with coverage
    exit_code = run_tests(coverage=True, verbose=True)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    # Check if coverage report was generated
    coverage_file = Path("htmlcov/index.html")
    if coverage_file.exists():
        print(f"📊 Coverage report generated: {coverage_file.absolute()}")
    
    # Check if XML coverage report was generated (for CI)
    xml_coverage = Path("coverage.xml")
    if xml_coverage.exists():
        print(f"📄 XML coverage report: {xml_coverage.absolute()}")


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Newsletter Test Runner")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--test",
        help="Specific test file or function to run"
    )
    parser.add_argument(
        "--markers", "-m",
        help="Pytest markers to filter tests"
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linting checks only"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security checks only"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (unit tests without coverage)"
    )
    
    args = parser.parse_args()
    
    if args.lint:
        return run_linting()
    
    if args.security:
        return run_security_checks()
    
    if args.report:
        generate_test_report()
        return 0
    
    if args.quick:
        return run_tests(
            test_type="unit",
            coverage=False,
            verbose=args.verbose,
            parallel=args.parallel,
            markers="not slow"
        )
    
    return run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        verbose=args.verbose,
        parallel=args.parallel,
        specific_test=args.test,
        markers=args.markers
    )


if __name__ == "__main__":
    sys.exit(main())

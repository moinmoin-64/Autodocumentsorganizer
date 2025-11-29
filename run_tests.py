#!/usr/bin/env python
"""
Test Runner Script
Führt Tests aus und generiert Coverage-Reports
"""
import sys
import subprocess
from pathlib import Path


def run_tests(test_type='all', verbose=True, coverage=True):
    """
    Führt Tests aus
    
    Args:
        test_type: 'unit', 'integration', 'e2e', oder 'all'
        verbose: Verbose output
        coverage: Coverage-Report generieren
    """
    cmd = ['pytest']
    
    # Verbose
    if verbose:
        cmd.append('-v')
    
    # Coverage
    if coverage:
        cmd.extend(['--cov=app', '--cov-report=html', '--cov-report=term-missing'])
    
    # Test-Typ
    if test_type == 'unit':
        cmd.extend(['-m', 'unit', 'tests/unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration', 'tests/integration'])
    elif test_type == 'e2e':
        cmd.extend(['-m', 'e2e', 'tests/e2e'])
    elif test_type == 'fast':
        cmd.extend(['-m', 'not slow'])
    else:
        cmd.append('tests/')
    
    print(f"🧪 Running tests: {test_type}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        if coverage:
            print("\n📊 Coverage report: file://htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
    
    return result.returncode


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests with various options')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'e2e', 'fast'],
        help='Type of tests to run'
    )
    parser.add_argument(
        '--no-cov',
        action='store_true',
        help='Disable coverage reporting'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Less verbose output'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel'
    )
    
    args = parser.parse_args()
    
    # Prüfe ob pytest installiert ist
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed!")
        print("Install with: pip install -r requirements-dev.txt")
        return 1
    
    # Run tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=not args.quiet,
        coverage=not args.no_cov
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

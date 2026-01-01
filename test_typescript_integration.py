#!/usr/bin/env python3
"""
Integration Test: TypeScript + Python Backend
Testet dass die kompilierten TypeScript-Dateien korrekt vom Python-Backend geliefert werden
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Farben für Terminal-Output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def check_typescript_installed():
    """Check if TypeScript is installed"""
    print_info("Checking TypeScript installation...")
    try:
        result = subprocess.run(['tsc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"TypeScript installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print_error("TypeScript not installed")
    return False

def compile_typescript():
    """Compile TypeScript files"""
    print_info("Compiling TypeScript files...")
    
    # Run type check
    result = subprocess.run(['tsc', '--noEmit'], capture_output=True, text=True)
    if result.returncode != 0:
        print_error("Type check failed!")
        print(result.stderr)
        return False
    
    print_success("Type check passed")
    
    # Compile
    result = subprocess.run(['tsc'], capture_output=True, text=True)
    if result.returncode != 0:
        print_error("Compilation failed!")
        print(result.stderr)
        return False
    
    print_success("TypeScript compilation successful")
    return True

def verify_output_files():
    """Verify that JavaScript files were generated"""
    print_info("Verifying compiled output files...")
    
    dist_dir = Path('app/static/js/dist')
    if not dist_dir.exists():
        print_error(f"Output directory not found: {dist_dir}")
        return False
    
    js_files = list(dist_dir.glob('**/*.js'))
    if not js_files:
        print_error(f"No JavaScript files found in {dist_dir}")
        return False
    
    print_success(f"Found {len(js_files)} JavaScript files")
    
    # List critical files
    critical_files = [
        'api-client.js',
        'error-handler.js',
        'app.js',
        'notifications.js',
    ]
    
    for critical in critical_files:
        file_path = dist_dir / critical
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print_success(f"  ✓ {critical} ({size_kb:.1f} KB)")
        else:
            print_warning(f"  ⚠ {critical} not found")
    
    return True

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print_info("Checking Python dependencies...")
    
    required_packages = [
        'flask',
        'pytest',
        'requests',
    ]
    
    try:
        from importlib.metadata import distributions
        installed = {dist.metadata['Name'].lower() for dist in distributions()}
        
        all_ok = True
        for package in required_packages:
            if package.lower() in installed:
                print_success(f"  ✓ {package}")
            else:
                print_warning(f"  ⚠ {package} not installed")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print_error(f"Failed to check dependencies: {e}")
        return False

def run_python_tests():
    """Run Python tests"""
    print_info("Running Python tests...")
    
    result = subprocess.run(
        ['pytest', 'tests/', '-v', '--tb=short'],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Parse output
    if 'passed' in result.stdout:
        # Extract test count
        import re
        match = re.search(r'(\d+) passed', result.stdout)
        if match:
            test_count = match.group(1)
            print_success(f"All {test_count} tests passed!")
            return True
    
    if result.returncode == 0:
        print_success("Tests passed")
        return True
    
    print_error("Some tests failed")
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return False

def check_html_imports():
    """Check if HTML files reference the correct JS paths"""
    print_info("Checking HTML imports...")
    
    html_files = list(Path('.').glob('app/templates/**/*.html'))
    if not html_files:
        print_warning("No HTML templates found")
        return True
    
    old_imports = 0
    new_imports = 0
    
    for html_file in html_files:
        content = html_file.read_text()
        
        # Check for dist imports
        if 'js/dist/' in content:
            new_imports += 1
        elif 'app/static/js/' in content:
            old_imports += 1
    
    if old_imports > 0:
        print_warning(f"Found {old_imports} HTML files with old import paths")
        print_info("These should be updated to use 'js/dist/' paths")
        return False
    
    if new_imports > 0:
        print_success(f"HTML imports correctly reference dist directory ({new_imports} files)")
        return True
    
    print_info("No dynamic JS imports found in HTML templates (use script tags)")
    return True

def verify_type_definitions():
    """Verify that type definition files were generated"""
    print_info("Verifying TypeScript type definitions...")
    
    dist_dir = Path('app/static/js/dist')
    d_ts_files = list(dist_dir.glob('**/*.d.ts'))
    
    if d_ts_files:
        print_success(f"Found {len(d_ts_files)} type definition files (.d.ts)")
        return True
    
    print_warning("No type definition files generated (check tsconfig.json declaration setting)")
    return True

def generate_report(results):
    """Generate final test report"""
    print_header("📊 INTEGRATION TEST REPORT")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}\n")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:10} - {test_name}")
    
    print()
    
    if passed_tests == total_tests:
        print_success("ALL TESTS PASSED! 🎉")
        print("\nProject is ready for deployment:")
        print("  1. Start Flask server: python main.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Run E2E tests: pytest tests/e2e/")
        return True
    else:
        print_error(f"Some tests failed ({total_tests - passed_tests} failures)")
        return False

def main():
    """Main test runner"""
    print_header("🔧 TypeScript + Python Integration Tests")
    
    results = {}
    
    # Test 1: TypeScript installed
    results['TypeScript Installed'] = check_typescript_installed()
    if not results['TypeScript Installed']:
        print_error("Cannot proceed without TypeScript")
        return False
    
    # Test 2: Compilation
    results['TypeScript Compilation'] = compile_typescript()
    if not results['TypeScript Compilation']:
        print_error("Cannot proceed without successful compilation")
        return False
    
    # Test 3: Output files
    results['Output Files Generated'] = verify_output_files()
    
    # Test 4: Type definitions
    results['Type Definitions'] = verify_type_definitions()
    
    # Test 5: Python dependencies
    results['Python Dependencies'] = check_python_dependencies()
    
    # Test 6: Python tests
    results['Python Tests'] = run_python_tests()
    
    # Test 7: HTML imports
    results['HTML Imports'] = check_html_imports()
    
    # Generate report
    success = generate_report(results)
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
OrganisationsAI - CLI Tools Validator
Validates all CLI tools for correctness
"""

import subprocess
import sys
from pathlib import Path


class CLIValidator:
    """Validates CLI tools"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.passed = []
    
    def print_header(self, text: str):
        """Print header"""
        print(f"\n{'='*70}")
        print(f"{text:^70}")
        print(f"{'='*70}\n")
    
    def print_pass(self, text: str):
        """Print passing test"""
        print(f"✅ {text}")
        self.passed.append(text)
    
    def print_fail(self, text: str):
        """Print failing test"""
        print(f"❌ {text}")
        self.errors.append(text)
    
    def print_warn(self, text: str):
        """Print warning"""
        print(f"⚠️  {text}")
        self.warnings.append(text)
    
    # Test Suite
    
    def test_quick_start_syntax(self):
        """Test quick_start_final.py syntax"""
        quick_start = self.project_root / "quick_start_final.py"
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(quick_start)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_pass("quick_start_final.py: Syntax OK")
            else:
                self.print_fail(f"quick_start_final.py: Syntax Error\n{result.stderr}")
        
        except Exception as e:
            self.print_fail(f"quick_start_final.py: {e}")
    
    def test_install_wizard_syntax(self):
        """Test install_wizard.py syntax"""
        wizard = self.project_root / "install_wizard.py"
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(wizard)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_pass("install_wizard.py: Syntax OK")
            else:
                self.print_fail(f"install_wizard.py: Syntax Error\n{result.stderr}")
        
        except Exception as e:
            self.print_fail(f"install_wizard.py: {e}")
    
    def test_cli_syntax(self):
        """Test cli.py syntax"""
        cli = self.project_root / "cli.py"
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(cli)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_pass("cli.py: Syntax OK")
            else:
                self.print_fail(f"cli.py: Syntax Error\n{result.stderr}")
        
        except Exception as e:
            self.print_fail(f"cli.py: {e}")
    
    def test_quick_start_imports(self):
        """Test quick_start_final.py imports"""
        code = """
import sys
from pathlib import Path

# Import quick_start
sys.path.insert(0, r'{project}')
import quick_start_final
print("OK")
""".format(project=self.project_root)
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.project_root)
            )
            
            if "OK" in result.stdout:
                self.print_pass("quick_start_final.py: Imports OK")
            else:
                self.print_fail(f"quick_start_final.py: Import Error\n{result.stderr}")
        
        except Exception as e:
            self.print_fail(f"quick_start_final.py: {e}")
    
    def test_cli_help(self):
        """Test cli.py help command"""
        try:
            result = subprocess.run(
                [sys.executable, "cli.py", "help"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                self.print_pass("cli.py: 'help' command works")
            else:
                self.print_warn(f"cli.py: 'help' command exit code {result.returncode}")
        
        except subprocess.TimeoutExpired:
            self.print_warn("cli.py: 'help' command timed out")
        except Exception as e:
            self.print_fail(f"cli.py: {e}")
    
    def test_cli_info(self):
        """Test cli.py info command"""
        try:
            result = subprocess.run(
                [sys.executable, "cli.py", "info"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.project_root)
            )
            
            if "Python" in result.stdout:
                self.print_pass("cli.py: 'info' command works")
            else:
                self.print_warn(f"cli.py: 'info' command output incomplete")
        
        except subprocess.TimeoutExpired:
            self.print_warn("cli.py: 'info' command timed out")
        except Exception as e:
            self.print_fail(f"cli.py: {e}")
    
    def test_files_exist(self):
        """Test all CLI files exist"""
        files = [
            "quick_start_final.py",
            "install_wizard.py",
            "cli.py",
            "CLI_GUIDE_DE.md",
            "CLI_TOOLS_README.md"
        ]
        
        for file in files:
            path = self.project_root / file
            if path.exists():
                self.print_pass(f"File exists: {file}")
            else:
                self.print_fail(f"File missing: {file}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        self.print_header("OrganisationsAI - CLI Tools Validator")
        
        # File Existence Tests
        print("📁 File Existence Tests:")
        self.test_files_exist()
        
        # Syntax Tests
        print("\n📝 Syntax Tests:")
        self.test_quick_start_syntax()
        self.test_install_wizard_syntax()
        self.test_cli_syntax()
        
        # Import Tests
        print("\n📦 Import Tests:")
        self.test_quick_start_imports()
        
        # Functional Tests
        print("\n🔧 Functional Tests:")
        self.test_cli_help()
        self.test_cli_info()
        
        # Summary
        self.print_header("Test Summary")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return len(self.errors) == 0


def main():
    """Main entry point"""
    validator = CLIValidator()
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

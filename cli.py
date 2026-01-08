#!/usr/bin/env python3
"""
OrganisationsAI - Management CLI
Command-line interface for application management
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List
from enum import Enum
import platform


class Colors:
    """ANSI Color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CLIManager:
    """Command-line management interface"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.platform = platform.system()
        self.python_exe = self._get_python_exe()
        
    def _get_python_exe(self) -> str:
        """Get Python executable from virtual environment"""
        venv_path = self.project_root / ".venv"
        if self.platform == "Windows":
            return str(venv_path / "Scripts" / "python.exe")
        else:
            return str(venv_path / "bin" / "python")
    
    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}[OK]{Colors.ENDC} {text}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {text}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {text}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {text}")
    
    def run_command(self, cmd: List[str], description: str = "") -> bool:
        """Run command"""
        try:
            if description:
                print(f"{Colors.CYAN}→ {description}...{Colors.ENDC}")
            
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        except Exception as e:
            self.print_error(f"{e}")
            return False
    
    # ========== Development Commands ==========
    
    def dev_run(self, args):
        """Start development server"""
        self.print_header("Development Server")
        self.print_info(f"Starting on http://localhost:5000")
        self.run_command([self.python_exe, "main.py"])
    
    def dev_shell(self, args):
        """Start Python shell with app context"""
        self.print_header("Python Shell")
        cmd = [self.python_exe, "-i", "-c"]
        code = "from app.server import create_app; app = create_app(); ctx = app.app_context(); ctx.push()"
        self.run_command(cmd + [code])
    
    def dev_lint(self, args):
        """Run linting checks"""
        self.print_header("Code Linting")
        
        self.print_info("Running pylint...")
        self.run_command(
            [self.python_exe, "-m", "pylint", "app/"],
            "Pylint"
        )
    
    def dev_format(self, args):
        """Format code with black"""
        self.print_header("Code Formatting")
        
        self.print_info("Formatting with black...")
        self.run_command(
            [self.python_exe, "-m", "black", "app/"],
            "Black"
        )
    
    # ========== Testing Commands ==========
    
    def test_unit(self, args):
        """Run unit tests"""
        self.print_header("Unit Tests")
        
        self.run_command(
            [self.python_exe, "-m", "pytest", "tests/", "-v"],
            "Unit Tests"
        )
    
    def test_coverage(self, args):
        """Run tests with coverage report"""
        self.print_header("Coverage Report")
        
        self.run_command(
            [self.python_exe, "-m", "pytest", "tests/", "--cov=app", "--cov-report=html"],
            "Coverage Analysis"
        )
    
    def test_e2e(self, args):
        """Run end-to-end tests"""
        self.print_header("End-to-End Tests")
        
        self.run_command(
            [self.python_exe, "-m", "pytest", "tests/", "-k", "e2e", "-v"],
            "E2E Tests"
        )
    
    # ========== Database Commands ==========
    
    def db_init(self, args):
        """Initialize database"""
        self.print_header("Database Initialization")
        
        code = """
from app.db_config import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('[OK] Database initialized')
"""
        self.run_command([self.python_exe, "-c", code])
    
    def db_migrate(self, args):
        """Run database migrations"""
        self.print_header("Database Migrations")
        
        print(f"{Colors.YELLOW}Note: Alembic migrations not yet configured{Colors.ENDC}")
        print("Run: alembic upgrade head")
    
    def db_clean(self, args):
        """Clean database (development only)"""
        self.print_header("Database Clean")
        self.print_warning("This will delete all data!")
        
        confirm = input(f"{Colors.RED}Type 'DELETE' to confirm: {Colors.ENDC}")
        if confirm != "DELETE":
            self.print_info("Aborted")
            return
        
        code = """
from app.db_config import engine
from app.models import Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('[OK] Database cleaned')
"""
        self.run_command([self.python_exe, "-c", code])
    
    def db_backup(self, args):
        """Backup database"""
        self.print_header("Database Backup")
        
        from datetime import datetime
        backup_dir = self.project_root / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_file = self.project_root / "data" / "database.db"
        backup_file = backup_dir / f"database_{timestamp}.db"
        
        if db_file.exists():
            import shutil
            shutil.copy2(db_file, backup_file)
            self.print_success(f"Database backed up: {backup_file}")
        else:
            self.print_error(f"Database not found: {db_file}")
    
    # ========== Build Commands ==========
    
    def build_typescript(self, args):
        """Build TypeScript files"""
        self.print_header("TypeScript Build")
        
        npm_cmd = "npm.cmd" if self.platform == "Windows" else "npm"
        self.run_command([npm_cmd, "run", "compile"], "TypeScript Compilation")
    
    def build_docker(self, args):
        """Build Docker image"""
        self.print_header("Docker Build")
        
        version = args.version or "latest"
        self.run_command(
            ["docker", "build", "-t", f"organisationsai:{version}", "."],
            f"Docker Build (v{version})"
        )
    
    # ========== Deployment Commands ==========
    
    def deploy_docker(self, args):
        """Deploy with Docker"""
        self.print_header("Docker Deployment")
        
        port = args.port or "5000"
        env_file = args.env or ".env"
        
        cmd = [
            "docker", "run",
            "-d",
            "--name", "organisationsai",
            f"-p", f"{port}:5000",
            "--env-file", env_file,
            "organisationsai:latest"
        ]
        
        self.run_command(cmd, "Docker Run")
    
    def deploy_kubernetes(self, args):
        """Deploy with Kubernetes"""
        self.print_header("Kubernetes Deployment")
        
        namespace = args.namespace or "default"
        
        self.run_command(
            ["kubectl", "apply", "-f", "k8s/", "-n", namespace],
            "Kubernetes Deploy"
        )
    
    # ========== Utility Commands ==========
    
    def info(self, args):
        """Show system information"""
        self.print_header("System Information")
        
        import platform as plat
        
        info_items = [
            ("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
            ("Platform", f"{plat.system()} {plat.release()}"),
            ("Project Root", str(self.project_root)),
            ("Virtual Env", str(self.project_root / ".venv")),
            ("Config File", str(self.project_root / "config.yaml")),
            ("Env File", str(self.project_root / ".env")),
        ]
        
        for name, value in info_items:
            print(f"{Colors.CYAN}{name:.<30}{Colors.ENDC} {value}")
    
    def help_extended(self, args):
        """Show extended help"""
        self.print_header("Extended Help")
        
        print("""
DEVELOPMENT COMMANDS:
  dev run          Start development server (http://localhost:5000)
  dev shell        Start interactive Python shell with app context
  dev lint         Run code linting checks (pylint)
  dev format       Format code with black

TESTING COMMANDS:
  test unit        Run unit tests
  test coverage    Run tests with coverage report
  test e2e         Run end-to-end tests

DATABASE COMMANDS:
  db init          Initialize database
  db migrate       Run database migrations
  db clean         Clean database (WARNING: deletes data!)
  db backup        Backup current database

BUILD COMMANDS:
  build ts         Build TypeScript files
  build docker     Build Docker image

DEPLOYMENT COMMANDS:
  deploy docker    Deploy with Docker
  deploy k8s       Deploy with Kubernetes

UTILITY COMMANDS:
  info             Show system information
  help             Show this help
        """)
    
    def main(self):
        """Main CLI interface"""
        parser = argparse.ArgumentParser(
            description="OrganisationsAI Management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s dev run
  %(prog)s test unit
  %(prog)s db backup
  %(prog)s build docker --version 1.0.0
  %(prog)s deploy docker --port 8000
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Development commands
        dev_parser = subparsers.add_parser("dev", help="Development commands")
        dev_subparsers = dev_parser.add_subparsers(dest="dev_command")
        dev_subparsers.add_parser("run", help="Run development server")
        dev_subparsers.add_parser("shell", help="Start Python shell")
        dev_subparsers.add_parser("lint", help="Run linting")
        dev_subparsers.add_parser("format", help="Format code")
        
        # Testing commands
        test_parser = subparsers.add_parser("test", help="Testing commands")
        test_subparsers = test_parser.add_subparsers(dest="test_command")
        test_subparsers.add_parser("unit", help="Run unit tests")
        test_subparsers.add_parser("coverage", help="Run tests with coverage")
        test_subparsers.add_parser("e2e", help="Run E2E tests")
        
        # Database commands
        db_parser = subparsers.add_parser("db", help="Database commands")
        db_subparsers = db_parser.add_subparsers(dest="db_command")
        db_subparsers.add_parser("init", help="Initialize database")
        db_subparsers.add_parser("migrate", help="Run migrations")
        db_subparsers.add_parser("clean", help="Clean database")
        db_subparsers.add_parser("backup", help="Backup database")
        
        # Build commands
        build_parser = subparsers.add_parser("build", help="Build commands")
        build_subparsers = build_parser.add_subparsers(dest="build_command")
        build_subparsers.add_parser("ts", help="Build TypeScript")
        docker_parser = build_subparsers.add_parser("docker", help="Build Docker image")
        docker_parser.add_argument("--version", "-v", help="Docker image version")
        
        # Deployment commands
        deploy_parser = subparsers.add_parser("deploy", help="Deployment commands")
        deploy_subparsers = deploy_parser.add_subparsers(dest="deploy_command")
        docker_deploy = deploy_subparsers.add_parser("docker", help="Deploy with Docker")
        docker_deploy.add_argument("--port", "-p", help="Port number")
        docker_deploy.add_argument("--env", "-e", help="Environment file")
        k8s_deploy = deploy_subparsers.add_parser("k8s", help="Deploy with Kubernetes")
        k8s_deploy.add_argument("--namespace", "-n", help="Kubernetes namespace")
        
        # Utility commands
        subparsers.add_parser("info", help="Show system information")
        subparsers.add_parser("help", help="Show extended help")
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Route commands
        try:
            if args.command == "dev":
                if args.dev_command == "run":
                    self.dev_run(args)
                elif args.dev_command == "shell":
                    self.dev_shell(args)
                elif args.dev_command == "lint":
                    self.dev_lint(args)
                elif args.dev_command == "format":
                    self.dev_format(args)
            
            elif args.command == "test":
                if args.test_command == "unit":
                    self.test_unit(args)
                elif args.test_command == "coverage":
                    self.test_coverage(args)
                elif args.test_command == "e2e":
                    self.test_e2e(args)
            
            elif args.command == "db":
                if args.db_command == "init":
                    self.db_init(args)
                elif args.db_command == "migrate":
                    self.db_migrate(args)
                elif args.db_command == "clean":
                    self.db_clean(args)
                elif args.db_command == "backup":
                    self.db_backup(args)
            
            elif args.command == "build":
                if args.build_command == "ts":
                    self.build_typescript(args)
                elif args.build_command == "docker":
                    self.build_docker(args)
            
            elif args.command == "deploy":
                if args.deploy_command == "docker":
                    self.deploy_docker(args)
                elif args.deploy_command == "k8s":
                    self.deploy_kubernetes(args)
            
            elif args.command == "info":
                self.info(args)
            
            elif args.command == "help":
                self.help_extended(args)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Aborted.{Colors.ENDC}")
            sys.exit(1)
        except Exception as e:
            self.print_error(f"{e}")
            sys.exit(1)


def main():
    """Main entry point"""
    cli = CLIManager()
    cli.main()


if __name__ == "__main__":
    main()

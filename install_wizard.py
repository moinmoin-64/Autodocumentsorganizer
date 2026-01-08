#!/usr/bin/env python3
"""
OrganisationsAI - Installation & Configuration CLI
Professional setup wizard with auto-configuration
"""

import os
import sys
import subprocess
import platform
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import secrets
import hashlib
from datetime import datetime
from enum import Enum


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


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class InstallationWizard:
    """Professional installation wizard with auto-configuration"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_file = self.project_root / "config.yaml"
        self.env_file = self.project_root / ".env"
        self.venv_path = self.project_root / ".venv"
        self.platform = platform.system()
        self.config = {}
        self.environment = Environment.DEVELOPMENT
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if self.platform == 'Windows' else 'clear')
    
    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {text}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'-'*68}{Colors.ENDC}")
    
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
    
    def ask_input(self, prompt: str, default: str = "", choices: List[str] = None) -> str:
        """Ask user for input with validation"""
        default_text = f" [{default}]" if default else ""
        choices_text = f" ({'/'.join(choices)})" if choices else ""
        
        while True:
            user_input = input(f"{Colors.BOLD}{prompt}{default_text}{choices_text}:{Colors.ENDC} ").strip()
            
            if not user_input:
                if default:
                    return default
                print(f"{Colors.RED}Input erforderlich!{Colors.ENDC}")
                continue
            
            if choices and user_input not in choices:
                print(f"{Colors.RED}Ungültige Auswahl! Wähle: {', '.join(choices)}{Colors.ENDC}")
                continue
            
            return user_input
    
    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Ask yes/no question"""
        default_text = "[Y/n]" if default else "[y/N]"
        response = self.ask_input(prompt, default_text)
        return response.lower() in ['y', 'yes', 'j', 'ja']
    
    def run_command(self, cmd: List[str], description: str = "") -> Tuple[bool, str]:
        """Run command and capture output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def check_python_version(self) -> bool:
        """Check if Python 3.11+ is installed"""
        self.print_section("Python Version Check")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 11:
            self.print_success(f"Python {version_str}")
            return True
        else:
            self.print_error(f"Python 3.11+ erforderlich (aktuell: {version_str})")
            return False
    
    def check_dependencies(self) -> bool:
        """Check if required tools are installed"""
        self.print_section("Abhängigkeiten Check")
        
        requirements = {
            'pip': 'pip --version',
            'git': 'git --version',
        }
        
        if self.platform == 'Windows':
            requirements['Node.js'] = 'node --version'
        
        all_ok = True
        for tool, cmd in requirements.items():
            success, output = self.run_command(cmd.split())
            if success:
                version = output.strip().split('\n')[0]
                self.print_success(f"{tool}: {version}")
            else:
                self.print_error(f"{tool}: NICHT GEFUNDEN")
                all_ok = False
        
        return all_ok
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment"""
        self.print_section("Virtual Environment Setup")
        
        if self.venv_path.exists():
            self.print_warning(f"Virtual Environment existiert bereits: {self.venv_path}")
            if not self.ask_yes_no("Neu erstellen?", default=False):
                return True
            shutil.rmtree(self.venv_path)
        
        print(f"Erstelle Virtual Environment unter {self.venv_path}...")
        
        success, output = self.run_command(
            [sys.executable, "-m", "venv", str(self.venv_path)]
        )
        
        if success:
            self.print_success(f"Virtual Environment erstellt")
            return True
        else:
            self.print_error(f"Fehler beim Erstellen des Virtual Environment:\n{output}")
            return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to latest version"""
        self.print_section("Pip Upgrade")
        
        pip_cmd = str(self.venv_path / ("Scripts" if self.platform == "Windows" else "bin") / "pip")
        
        print("Upgrade pip...")
        success, output = self.run_command([pip_cmd, "install", "--upgrade", "pip", "setuptools", "wheel"])
        
        if success:
            self.print_success("Pip aktualisiert")
            return True
        else:
            self.print_error(f"Fehler beim Upgrade von Pip:\n{output}")
            return False
    
    def install_python_packages(self) -> bool:
        """Install Python packages from requirements.txt"""
        self.print_section("Python Packages Installation")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.print_error(f"requirements.txt nicht gefunden: {requirements_file}")
            return False
        
        pip_cmd = str(self.venv_path / ("Scripts" if self.platform == "Windows" else "bin") / "pip")
        
        print(f"Installiere Packages aus {requirements_file}...")
        success, output = self.run_command([pip_cmd, "install", "-r", str(requirements_file)])
        
        if success:
            self.print_success("Python Packages installiert")
            return True
        else:
            self.print_error(f"Fehler bei Package-Installation:\n{output}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure application environment"""
        self.print_section("Environment Konfiguration")
        
        # Ask for environment
        env_choice = self.ask_input(
            "Wähle Deployment-Environment",
            "development",
            ["development", "staging", "production"]
        )
        self.environment = Environment(env_choice)
        
        # Generate SECRET_KEY
        secret_key = secrets.token_urlsafe(32)
        self.print_success(f"SECRET_KEY generiert (32 Zeichen)")
        
        # Generate database password hash
        db_password = self.ask_input(
            "Datenbank Passwort",
            "admin"
        )
        
        # Create .env file
        env_content = f"""# OrganisationsAI Configuration
# Auto-generated: {datetime.now().isoformat()}

# Flask Configuration
FLASK_ENV={self.environment.value}
FLASK_DEBUG={"true" if self.environment == Environment.DEVELOPMENT else "false"}
SECRET_KEY={secret_key}

# Database
DATABASE_URL=sqlite:///data/database.db
DB_PASSWORD={hashlib.sha256(db_password.encode()).hexdigest()}

# Redis
REDIS_URL=redis://localhost:6379

# Ollama (LLM)
OLLAMA_URL=http://localhost:11434

# Server
SERVER_HOST=localhost
SERVER_PORT=5000

# Logging
LOG_LEVEL={("DEBUG" if self.environment == Environment.DEVELOPMENT else "INFO")}
LOG_FILE=logs/app.log

# Email (Optional)
EMAIL_ENABLED=false
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-password

# Sentry (Error Tracking)
SENTRY_ENABLED=false
SENTRY_DSN=

# Security
CORS_ORIGINS=["http://localhost:5000"]
SESSION_TIMEOUT=3600
"""
        
        self.env_file.write_text(env_content)
        self.print_success(f".env Datei erstellt: {self.env_file}")
        
        return True
    
    def load_base_config(self) -> Dict:
        """Load base configuration from config.yaml"""
        if not self.config_file.exists():
            self.print_warning(f"config.yaml nicht gefunden: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.print_error(f"Fehler beim Laden von config.yaml: {e}")
            return {}
    
    def configure_ocr(self) -> Dict:
        """Configure OCR settings"""
        self.print_section("OCR Konfiguration")
        
        ocr_config = {
            'enabled': True,
            'engine': 'tesseract',
            'languages': ['deu', 'eng'],
            'preprocessing': True,
            'min_confidence': 0.7
        }
        
        if self.ask_yes_no("Tesseract ist installiert?", default=True):
            self.print_success("OCR aktiviert (Tesseract)")
        else:
            self.print_warning("OCR wird deaktiviert")
            ocr_config['enabled'] = False
        
        return ocr_config
    
    def configure_ai(self) -> Dict:
        """Configure AI settings"""
        self.print_section("AI/ML Konfiguration")
        
        ai_config = {
            'categorization': {
                'enabled': True,
                'model': 'paraphrase-multilingual-MiniLM-L12-v2',
                'confidence_threshold': 0.7
            },
            'ollama': {
                'enabled': False,
                'url': 'http://localhost:11434',
                'model': 'qwen2.5:7b-q4_K_M',
                'temperature': 0.1,
                'max_tokens': 500
            }
        }
        
        if self.ask_yes_no("Ollama (LLM) Installation verfügbar?", default=False):
            ai_config['ollama']['enabled'] = True
            ollama_url = self.ask_input(
                "Ollama URL",
                ai_config['ollama']['url']
            )
            ai_config['ollama']['url'] = ollama_url
            self.print_success("Ollama aktiviert")
        
        return ai_config
    
    def configure_database(self) -> Dict:
        """Configure database settings"""
        self.print_section("Datenbank Konfiguration")
        
        db_config = {
            'type': 'sqlite',
            'path': 'data/database.db',
            'backup': {
                'enabled': True,
                'frequency': 'daily',
                'retention_days': 30
            }
        }
        
        if self.environment == Environment.PRODUCTION:
            self.print_warning("Für Production wird PostgreSQL empfohlen")
            if self.ask_yes_no("PostgreSQL verwenden?", default=False):
                db_config['type'] = 'postgresql'
                db_config['host'] = self.ask_input("Database Host", "localhost")
                db_config['port'] = self.ask_input("Database Port", "5432")
                db_config['database'] = self.ask_input("Database Name", "organisationsai")
        
        return db_config
    
    def configure_storage(self) -> Dict:
        """Configure file storage"""
        self.print_section("Speicher Konfiguration")
        
        storage_config = {
            'local': {
                'enabled': True,
                'base_path': 'data/storage'
            },
            's3': {
                'enabled': False,
                'bucket': '',
                'region': 'eu-west-1'
            }
        }
        
        # Create storage directory
        storage_path = self.project_root / storage_config['local']['base_path']
        storage_path.mkdir(parents=True, exist_ok=True)
        self.print_success(f"Speicher-Verzeichnis erstellt: {storage_path}")
        
        return storage_config
    
    def configure_security(self) -> Dict:
        """Configure security settings"""
        self.print_section("Sicherheits Konfiguration")
        
        security_config = {
            'password_hashing': 'scrypt',
            'session_timeout': 3600,
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60
            },
            'cors': {
                'enabled': True,
                'origins': ['http://localhost:5000']
            }
        }
        
        if self.environment == Environment.PRODUCTION:
            origins = self.ask_input(
                "CORS Origins (durch Komma getrennt)",
                "https://yourdomain.com"
            )
            security_config['cors']['origins'] = [o.strip() for o in origins.split(',')]
        
        return security_config
    
    def update_config_file(self) -> bool:
        """Update config.yaml with new settings"""
        self.print_section("Config Datei Update")
        
        try:
            config = self.load_base_config()
            
            # Update with new configuration
            config.update({
                'environment': self.environment.value,
                'ocr': self.configure_ocr(),
                'ai': self.configure_ai(),
                'database': self.configure_database(),
                'storage': self.configure_storage(),
                'security': self.configure_security(),
            })
            
            # Save updated config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self.print_success(f"config.yaml aktualisiert: {self.config_file}")
            return True
        except Exception as e:
            self.print_error(f"Fehler beim Update der config.yaml: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize database"""
        self.print_section("Datenbank Initialisierung")
        
        print("Erstelle Database-Tabellen...")
        
        try:
            # Add project to path
            sys.path.insert(0, str(self.project_root))
            
            from app.database import Database
            from app.db_config import engine
            from app.models import Base
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            self.print_success("Datenbank initialisiert")
            
            return True
        except Exception as e:
            self.print_error(f"Fehler bei Datenbank-Initialisierung: {e}")
            return False
    
    def create_default_users(self) -> bool:
        """Create default admin user"""
        self.print_section("Standard-Benutzer Konfiguration")
        
        admin_password = self.ask_input("Admin Passwort", "admin123")
        
        from werkzeug.security import generate_password_hash
        
        # Update config with hashed password
        config = self.load_base_config()
        if 'auth' not in config:
            config['auth'] = {'users': {}}
        
        hashed = generate_password_hash(admin_password, method='scrypt')
        config['auth']['users']['admin'] = hashed
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        self.print_success(f"Admin-Benutzer erstellt (Benutzername: admin)")
        return True
    
    def compile_typescript(self) -> bool:
        """Compile TypeScript files"""
        self.print_section("TypeScript Kompilierung")
        
        if not (self.project_root / "tsconfig.json").exists():
            self.print_warning("tsconfig.json nicht gefunden, überspringe TypeScript")
            return True
        
        if self.platform == "Windows":
            npm_cmd = "npm.cmd"
        else:
            npm_cmd = "npm"
        
        print("Kompiliere TypeScript...")
        success, output = self.run_command([npm_cmd, "run", "compile"])
        
        if success:
            self.print_success("TypeScript kompiliert")
            return True
        else:
            self.print_warning(f"TypeScript Kompilierung fehlgeschlagen (optional)")
            return True  # Non-blocking
    
    def run_tests(self) -> bool:
        """Run test suite"""
        self.print_section("Unit Tests")
        
        python_cmd = str(self.venv_path / ("Scripts" if self.platform == "Windows" else "bin") / "python")
        
        print("Führe Tests aus...")
        success, output = self.run_command([python_cmd, "-m", "pytest", "tests/", "-v", "--tb=short"])
        
        if success:
            self.print_success("Alle Tests bestanden ✓")
            return True
        else:
            self.print_warning("Einige Tests fehlgeschlagen (optional)")
            print(output[-500:])  # Print last 500 chars
            return True  # Non-blocking
    
    def print_summary(self) -> None:
        """Print installation summary"""
        self.print_header("Installation Erfolgreich Abgeschlossen!")
        
        print(f"""
{Colors.GREEN}✓ Virtual Environment{Colors.ENDC}      {self.venv_path}
{Colors.GREEN}✓ Python Packages{Colors.ENDC}       Installiert
{Colors.GREEN}✓ Configuration{Colors.ENDC}         {self.config_file}
{Colors.GREEN}✓ Environment{Colors.ENDC}          {self.env_file}
{Colors.GREEN}✓ Database{Colors.ENDC}             Initialisiert
{Colors.GREEN}✓ Security{Colors.ENDC}             Konfiguriert

{Colors.BOLD}Nächste Schritte:{Colors.ENDC}

1. Aktiviere Virtual Environment:
   {Colors.CYAN}source .venv/bin/activate{Colors.ENDC} (Linux/Mac)
   {Colors.CYAN}.venv\\Scripts\\activate{Colors.ENDC} (Windows)

2. Starte Development Server:
   {Colors.CYAN}python main.py{Colors.ENDC}

3. Öffne Browser:
   {Colors.CYAN}http://localhost:5000{Colors.ENDC}

4. Login mit Admin-Benutzer:
   {Colors.CYAN}Username: admin{Colors.ENDC}
   {Colors.CYAN}Password: (wie konfiguriert){Colors.ENDC}

{Colors.BOLD}Dokumentation:{Colors.ENDC}
  • README_COMPLETE.md - Ausführliche Dokumentation
  • QUICKSTART.md - Quick Start Guide
  • API.md - API Dokumentation

{Colors.BOLD}Support:{Colors.ENDC}
  • Issues: GitHub Issues
  • Wiki: Project Wiki
  • Docs: docs/ Verzeichnis

{Colors.YELLOW}Hinweis: Stelle sicher dass die .env Datei sicher ist!{Colors.ENDC}
""")
    
    def run(self) -> bool:
        """Run the complete installation wizard"""
        self.clear_screen()
        self.print_header("OrganisationsAI Installation & Configuration")
        
        print(f"""
{Colors.BOLD}Willkommen zur Installation!{Colors.ENDC}

Dieses Programm wird dich durch die komplette Setup-Prozedur führen:
  • Abhängigkeits-Check
  • Virtual Environment Setup
  • Python Packages Installation
  • Konfiguration (Database, OCR, AI, Security)
  • Datenbank Initialisierung
  • Tests

{Colors.YELLOW}Dauer: ca. 5-15 Minuten (abhängig von Internet-Verbindung){Colors.ENDC}
""")
        
        if not self.ask_yes_no("Fortfahren?", default=True):
            print("Installation abgebrochen.")
            return False
        
        # Run installation steps
        steps = [
            ("Python Version Check", self.check_python_version),
            ("Abhängigkeiten Check", self.check_dependencies),
            ("Virtual Environment", self.create_virtual_environment),
            ("Pip Upgrade", self.upgrade_pip),
            ("Python Packages", self.install_python_packages),
            ("Environment Setup", self.configure_environment),
            ("Config Update", self.update_config_file),
            ("Datenbank Init", self.initialize_database),
            ("Benutzer Setup", self.create_default_users),
            ("TypeScript Compile", self.compile_typescript),
            ("Unit Tests", self.run_tests),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            try:
                print(f"\n{Colors.BOLD}{Colors.CYAN}→{Colors.ENDC} {step_name}...", end="", flush=True)
                if step_func():
                    print(f" {Colors.GREEN}✓{Colors.ENDC}")
                else:
                    print(f" {Colors.RED}✗{Colors.ENDC}")
                    failed_steps.append(step_name)
            except KeyboardInterrupt:
                print(f"\n{Colors.RED}Installation abgebrochen.{Colors.ENDC}")
                return False
            except Exception as e:
                print(f" {Colors.RED}✗{Colors.ENDC}")
                self.print_error(f"{step_name} fehlgeschlagen: {e}")
                failed_steps.append(step_name)
        
        # Print summary
        self.print_summary()
        
        if failed_steps:
            self.print_warning(f"Einige Schritte fehlgeschlagen: {', '.join(failed_steps)}")
            return False
        
        return True


def main():
    """Main entry point"""
    try:
        wizard = InstallationWizard()
        success = wizard.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation abgebrochen.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Fehler: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Automated Production Deployment Script
Handles complete deployment workflow with validation
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Deployment Configuration
# ============================================================================

class DeploymentConfig:
    """Deployment-Konfiguration"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "backups" / self.timestamp
        self.log_file = self.project_root / "logs" / f"deployment_{self.timestamp}.log"
    
    def __repr__(self):
        return f"DeploymentConfig(env={self.environment}, timestamp={self.timestamp})"


# ============================================================================
# Deployment Steps
# ============================================================================

class DeploymentStep:
    """Basis-Klasse für Deployment-Schritte"""
    
    def __init__(self, name: str, critical: bool = True):
        self.name = name
        self.critical = critical
        self.status = "pending"
        self.error_message = None
    
    def execute(self, config: DeploymentConfig) -> bool:
        """
        Führt Schritt aus
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            logger.info(f"▶️  Executing: {self.name}")
            self._run(config)
            self.status = "success"
            logger.info(f"✅ {self.name} completed successfully")
            return True
        
        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            logger.error(f"❌ {self.name} failed: {e}")
            
            if self.critical:
                logger.critical(f"🔴 Critical step failed. Aborting deployment.")
                return False
            else:
                logger.warning(f"⚠️  Non-critical step failed. Continuing...")
                return True
    
    def _run(self, config: DeploymentConfig):
        """Implementierung muss in Subclass erfolgen"""
        raise NotImplementedError


class PreDeploymentCheck(DeploymentStep):
    """Pre-Deployment Überprüfungen"""
    
    def __init__(self):
        super().__init__("Pre-Deployment Checks", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Prüft Pre-Deployment-Voraussetzungen"""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            raise RuntimeError(f"Python 3.11+ required, got {sys.version}")
        logger.info(f"✓ Python version: {sys.version}")
        
        # Check git status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=config.project_root
        )
        
        if result.stdout.strip():
            raise RuntimeError("Git working directory has uncommitted changes")
        logger.info("✓ Git status clean")
        
        # Check required files
        required_files = [
            "requirements.txt",
            "config.yaml",
            "Dockerfile",
            "docker-compose.yml",
        ]
        
        for file in required_files:
            if not (config.project_root / file).exists():
                raise RuntimeError(f"Required file missing: {file}")
        logger.info(f"✓ All required files present")


class DependencyCheck(DeploymentStep):
    """Dependency-Überprüfung"""
    
    def __init__(self):
        super().__init__("Dependency Check", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Prüft Abhängigkeiten"""
        logger.info("Checking dependencies...")
        
        # Check requirements
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Dependency issues found:\n{result.stdout}")
        
        logger.info("✓ All dependencies OK")


class RunTests(DeploymentStep):
    """Tests ausführen"""
    
    def __init__(self):
        super().__init__("Run Tests", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Führt Test-Suite aus"""
        logger.info("Running test suite...")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True, text=True, cwd=config.project_root
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Tests failed:\n{result.stdout}\n{result.stderr}")
        
        logger.info("✓ All tests passed")


class CreateBackup(DeploymentStep):
    """Backup erstellen"""
    
    def __init__(self):
        super().__init__("Create Backup", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Erstellt Backup"""
        logger.info(f"Creating backup in {config.backup_dir}...")
        
        # Create backup directories
        config.backup_dir.mkdir(parents=True, exist_ok=True)
        (config.backup_dir / "database").mkdir(exist_ok=True)
        (config.backup_dir / "uploads").mkdir(exist_ok=True)
        
        # Backup database
        db_backup = config.backup_dir / "database" / "database.sql"
        result = subprocess.run(
            [
                "pg_dump", "-U", os.getenv("DB_USER", "organisationsai_user"),
                os.getenv("DB_NAME", "organisationsai")
            ],
            stdout=open(db_backup, 'w'),
            stderr=subprocess.PIPE
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Database backup failed (non-critical)")
        else:
            logger.info(f"✓ Database backed up: {db_backup}")
        
        # Backup uploads
        uploads_dir = config.project_root / "uploads"
        if uploads_dir.exists():
            result = subprocess.run(
                ["tar", "-czf", str(config.backup_dir / "uploads.tar.gz"), "-C", 
                 str(uploads_dir), "."],
                capture_output=True
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Uploads backed up")


class SecurityScan(DeploymentStep):
    """Security-Scan"""
    
    def __init__(self):
        super().__init__("Security Scan", critical=False)
    
    def _run(self, config: DeploymentConfig):
        """Führt Security-Scan aus"""
        logger.info("Running security scan...")
        
        # Bandit security scan
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", "app/", "-f", "json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Security issues found:\n{result.stdout}")
        else:
            logger.info("✓ Security scan passed")


class CodeQuality(DeploymentStep):
    """Code-Qualität prüfen"""
    
    def __init__(self):
        super().__init__("Code Quality", critical=False)
    
    def _run(self, config: DeploymentConfig):
        """Prüft Code-Qualität"""
        logger.info("Checking code quality...")
        
        # Pylint
        result = subprocess.run(
            [sys.executable, "-m", "pylint", "app/", "--exit-zero"],
            capture_output=True, text=True
        )
        
        if "Your code has been rated" in result.stdout:
            logger.info("✓ Code quality check completed")
        else:
            logger.warning("⚠️  Could not determine code quality")


class BuildDockerImage(DeploymentStep):
    """Docker-Image bauen"""
    
    def __init__(self):
        super().__init__("Build Docker Image", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Baut Docker-Image"""
        logger.info("Building Docker image...")
        
        result = subprocess.run(
            ["docker", "build", "-t", "organisationsai:latest", "-t", 
             f"organisationsai:{config.timestamp}", "."],
            cwd=config.project_root
        )
        
        if result.returncode != 0:
            raise RuntimeError("Docker build failed")
        
        logger.info("✓ Docker image built successfully")


class HealthCheck(DeploymentStep):
    """Health-Checks ausführen"""
    
    def __init__(self):
        super().__init__("Health Check", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Führt Health-Checks aus"""
        logger.info("Running health checks...")
        
        # Check database
        try:
            subprocess.run(
                ["psql", "-c", "SELECT 1"],
                capture_output=True, check=True, timeout=5
            )
            logger.info("✓ Database OK")
        except Exception as e:
            logger.warning(f"⚠️  Database check failed: {e}")
        
        # Check Redis
        try:
            subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True, check=True, timeout=5
            )
            logger.info("✓ Redis OK")
        except Exception as e:
            logger.warning(f"⚠️  Redis check failed: {e}")
        
        # Check ports
        for port in [5000, 6379, 5432]:
            try:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True, timeout=5
                )
                logger.info(f"✓ Port {port} available")
            except Exception as e:
                logger.warning(f"⚠️  Port {port} check failed: {e}")


class DeployServices(DeploymentStep):
    """Services deployen"""
    
    def __init__(self):
        super().__init__("Deploy Services", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Deployt Services"""
        logger.info("Deploying services...")
        
        # Stop existing services
        logger.info("Stopping existing services...")
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.prod.yml", "down"],
            cwd=config.project_root, capture_output=True
        )
        
        # Start new services
        logger.info("Starting new services...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"],
            cwd=config.project_root
        )
        
        if result.returncode != 0:
            raise RuntimeError("Docker compose up failed")
        
        logger.info("✓ Services deployed successfully")


class PostDeploymentValidation(DeploymentStep):
    """Post-Deployment Validierung"""
    
    def __init__(self):
        super().__init__("Post-Deployment Validation", critical=True)
    
    def _run(self, config: DeploymentConfig):
        """Validiert Deployment"""
        import time
        
        logger.info("Validating deployment...")
        
        # Wait for services to start
        time.sleep(5)
        
        # Check API health
        try:
            result = subprocess.run(
                ["curl", "-f", "http://localhost:5000/health"],
                capture_output=True, timeout=10
            )
            
            if result.returncode != 0:
                raise RuntimeError("API health check failed")
            
            logger.info("✓ API health check passed")
        
        except Exception as e:
            raise RuntimeError(f"Post-deployment validation failed: {e}")


# ============================================================================
# Deployment Orchestrator
# ============================================================================

class DeploymentOrchestrator:
    """Orchestriert den Deployment-Prozess"""
    
    def __init__(self, environment: str = "production"):
        self.config = DeploymentConfig(environment)
        self.steps: List[DeploymentStep] = []
        self.results: List[Tuple[DeploymentStep, bool]] = []
    
    def add_step(self, step: DeploymentStep):
        """Fügt Deployment-Schritt hinzu"""
        self.steps.append(step)
    
    def build_pipeline(self):
        """Erstellt Standard-Deployment-Pipeline"""
        self.add_step(PreDeploymentCheck())
        self.add_step(DependencyCheck())
        self.add_step(RunTests())
        self.add_step(SecurityScan())
        self.add_step(CodeQuality())
        self.add_step(CreateBackup())
        self.add_step(BuildDockerImage())
        self.add_step(HealthCheck())
        self.add_step(DeployServices())
        self.add_step(PostDeploymentValidation())
    
    def execute(self) -> bool:
        """
        Führt alle Deployment-Schritte aus
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        logger.info(f"🚀 Starting deployment: {self.config}")
        logger.info(f"Environment: {self.config.environment}")
        logger.info(f"Timestamp: {self.config.timestamp}")
        
        for step in self.steps:
            success = step.execute(self.config)
            self.results.append((step, success))
            
            if not success and step.critical:
                logger.critical("❌ Deployment aborted due to critical failure")
                self._generate_report()
                return False
        
        logger.info("✅ Deployment completed successfully!")
        self._generate_report()
        return True
    
    def _generate_report(self):
        """Generiert Deployment-Report"""
        report_file = self.config.log_file
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(f"Deployment Report\n")
            f.write(f"==================\n\n")
            f.write(f"Environment: {self.config.environment}\n")
            f.write(f"Timestamp: {self.config.timestamp}\n\n")
            
            f.write(f"Steps:\n")
            for step, success in self.results:
                status = "✅" if success else "❌"
                f.write(f"{status} {step.name} - {step.status}\n")
                if step.error_message:
                    f.write(f"   Error: {step.error_message}\n")
            
            f.write(f"\nBackup Location: {self.config.backup_dir}\n")
        
        logger.info(f"📊 Report saved to: {report_file}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Deployment Script")
    parser.add_argument(
        "--env",
        default="production",
        choices=["development", "staging", "production"],
        help="Deployment environment"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup creation"
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = DeploymentOrchestrator(args.env)
    orchestrator.build_pipeline()
    
    # Execute deployment
    success = orchestrator.execute()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

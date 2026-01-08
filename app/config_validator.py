"""
Production Configuration Validator
Prüft ob Config für Production geeignet ist
"""

import logging
import os
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validiert Konfiguration für verschiedene Environments"""
    
    def __init__(self, config: Dict, environment: str = 'development'):
        self.config = config
        self.environment = environment
        self.issues: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """Validiert gesamte Konfiguration"""
        if self.environment == 'production':
            self._validate_production_config()
        else:
            self._validate_dev_config()
        
        return len(self.issues) == 0
    
    def _validate_production_config(self):
        """Strikte Prüfung für Production"""
        self._validate_secret_key(strict=True)
        self._validate_debug_mode()
        self._validate_database_config()
        self._validate_cors_origins()
        self._validate_logging()
        self._validate_security_headers()
    
    def _validate_dev_config(self):
        """Entspanntere Prüfung für Development"""
        self._validate_secret_key(strict=False)
        self._validate_database_config()
    
    def _validate_secret_key(self, strict: bool = False):
        """Prüft SECRET_KEY Konfiguration"""
        secret = os.getenv('SECRET_KEY', '')
        
        if not secret:
            if strict:
                self.issues.append("SECRET_KEY nicht als Environment-Variable gesetzt")
            else:
                self.warnings.append("SECRET_KEY nicht gesetzt, nutzt Default")
        
        default_key = 'dev-key-change-me-in-production'
        if secret == default_key or not secret:
            if strict:
                self.issues.append(f"SECRET_KEY nutzt Standardwert oder ist leer")
            else:
                self.warnings.append(f"SECRET_KEY ist Standard-Wert")
        
        if len(secret) < 32:
            self.warnings.append(f"SECRET_KEY sollte mindestens 32 Zeichen sein (aktuell: {len(secret)})")
    
    def _validate_debug_mode(self):
        """Prüft DEBUG-Mode"""
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        
        if debug:
            self.issues.append("FLASK_DEBUG=true nicht für Production geeignet")
    
    def _validate_database_config(self):
        """Prüft Database-Konfiguration"""
        db_config = self.config.get('database', {})
        
        if not db_config:
            self.warnings.append("Keine database-Konfiguration gefunden")
            return
        
        # Prüfe Datenbankpfad
        db_path = db_config.get('path', 'data/database.db')
        db_path_obj = Path(db_path)
        
        if not db_path_obj.parent.exists():
            if self.environment == 'production':
                self.issues.append(f"Database-Verzeichnis existiert nicht: {db_path_obj.parent}")
            else:
                self.warnings.append(f"Database-Verzeichnis wird erstellt: {db_path_obj.parent}")
        
        # Prüfe Backup-Konfiguration
        if self.environment == 'production':
            backup_enabled = db_config.get('backup', {}).get('enabled', False)
            if not backup_enabled:
                self.warnings.append("Database-Backup nicht aktiviert")
    
    def _validate_cors_origins(self):
        """Prüft CORS Konfiguration"""
        cors = self.config.get('web', {}).get('cors_origins', [])
        
        if '*' in cors:
            self.issues.append("CORS mit '*' (alle Origins) nicht für Production geeignet")
        
        if not cors and self.environment == 'production':
            self.warnings.append("Keine CORS-Origins konfiguriert")
    
    def _validate_logging(self):
        """Prüft Logging-Konfiguration"""
        log_config = self.config.get('logging', {})
        
        if not log_config:
            self.warnings.append("Keine logging-Konfiguration gefunden")
            return
        
        # Prüfe Log-Pfad
        log_file = log_config.get('file')
        if log_file:
            log_path = Path(log_file)
            if not log_path.parent.exists():
                if self.environment == 'production':
                    self.issues.append(f"Log-Verzeichnis existiert nicht: {log_path.parent}")
    
    def _validate_security_headers(self):
        """Prüft Security Headers Konfiguration"""
        security = self.config.get('security', {})
        
        headers = security.get('headers', {})
        if not headers:
            self.warnings.append("Security Headers nicht konfiguriert")
    
    def print_report(self):
        """Gibt Validierungsbericht aus"""
        if not self.issues and not self.warnings:
            logger.info("[OK] Konfiguration validiert - alle Checks bestanden")
            return
        
        if self.issues:
            logger.error(f"[ERROR] {len(self.issues)} Konfigurationsfehler gefunden:")
            for issue in self.issues:
                logger.error(f"  ❌ {issue}")
        
        if self.warnings:
            logger.warning(f"[WARNING] {len(self.warnings)} Warnungen:")
            for warning in self.warnings:
                logger.warning(f"  ⚠️  {warning}")
    
    def raise_if_invalid(self):
        """Wirft Exception wenn ungültig"""
        if self.issues:
            self.print_report()
            raise RuntimeError(f"{len(self.issues)} kritische Konfigurationsfehler gefunden")


def validate_production_config(config: Dict) -> bool:
    """Convenience-Function für Production-Validierung"""
    validator = ConfigValidator(config, environment='production')
    is_valid = validator.validate_all()
    validator.print_report()
    return is_valid

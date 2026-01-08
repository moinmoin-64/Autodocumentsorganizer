"""
Production Deployment & Configuration Management
Environment-specific configuration, secrets management, deployment validation
"""

import os
import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Environment & Deployment Modes
# ============================================================================

class Environment(Enum):
    """Deployment Environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database Configuration"""
    
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    echo: bool = False
    
    def __post_init__(self):
        """Validates configuration"""
        if not self.url:
            raise ValueError("Database URL is required")
        
        if self.pool_size < 1:
            raise ValueError("Pool size must be >= 1")


@dataclass
class CacheConfig:
    """Cache Configuration"""
    
    redis_url: str
    default_ttl: int = 3600
    max_connections: int = 50
    
    def __post_init__(self):
        """Validates configuration"""
        if not self.redis_url:
            raise ValueError("Redis URL is required")


@dataclass
class SecurityConfig:
    """Security Configuration"""
    
    secret_key: str
    allowed_origins: list
    enable_csrf: bool = True
    enable_rate_limiting: bool = True
    max_login_attempts: int = 5
    session_timeout: int = 3600
    password_min_length: int = 12
    password_require_special_chars: bool = True
    
    def __post_init__(self):
        """Validates configuration"""
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        
        if not self.allowed_origins:
            raise ValueError("At least one allowed origin is required")


@dataclass
class EmailConfig:
    """Email Configuration"""
    
    email_address: str
    email_password: str
    imap_server: str = "imap.gmail.com"
    imap_port: int = 993
    enable_ssl: bool = True
    enable_tls: bool = True
    
    def __post_init__(self):
        """Validates configuration"""
        if not all([self.imap_server, self.email_address, self.email_password]):
            raise ValueError("Email configuration incomplete")


@dataclass
class OCRConfig:
    """OCR Configuration"""
    
    enable_tesseract: bool = True
    enable_easyocr: bool = True
    enable_ollama: bool = True
    ollama_base_url: str = "http://localhost:11434"
    tesseract_path: Optional[str] = None
    confidence_threshold: float = 0.5
    
    def __post_init__(self):
        """Validates configuration"""
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            raise ValueError("Confidence threshold must be between 0 and 1")


@dataclass
class MonitoringConfig:
    """Monitoring Configuration"""
    
    enable_metrics: bool = True
    metrics_port: int = 8000
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_sentry: bool = False
    sentry_dsn: Optional[str] = None
    
    def __post_init__(self):
        """Validates configuration"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")


# ============================================================================
# Environment Configuration Management
# ============================================================================

class ConfigManager:
    """Verwaltet Umgebungskonfiguration"""
    
    def __init__(self, env: Environment = None):
        """
        Initialisiert ConfigManager
        
        Args:
            env: Environment (auto-detected if not provided)
        """
        self.env = env or self._detect_environment()
        self.config = self._load_environment_config()
    
    def _detect_environment(self) -> Environment:
        """Erkennt aktuelle Umgebung"""
        env_str = os.getenv('FLASK_ENV', 'development').lower()
        
        env_map = {
            'development': Environment.DEVELOPMENT,
            'staging': Environment.STAGING,
            'production': Environment.PRODUCTION,
            'testing': Environment.TESTING,
        }
        
        return env_map.get(env_str, Environment.DEVELOPMENT)
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Lädt Umgebungskonfiguration"""
        logger.info(f"📋 Loading {self.env.value} configuration")
        
        config = {}
        
        # Basis-Konfiguration
        config['DEBUG'] = self.env in [Environment.DEVELOPMENT, Environment.TESTING]
        config['TESTING'] = self.env == Environment.TESTING
        config['ENV'] = self.env.value
        
        # Database
        config['SQLALCHEMY_DATABASE_URI'] = self._get_database_url()
        config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }
        
        # Security
        config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        config['SESSION_COOKIE_SECURE'] = self.env == Environment.PRODUCTION
        config['SESSION_COOKIE_HTTPONLY'] = True
        config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        config['PERMANENT_SESSION_LIFETIME'] = 3600
        
        # CORS
        config['CORS_ALLOWED_ORIGINS'] = os.getenv('CORS_ALLOWED_ORIGINS', '*').split(',')
        
        # Upload
        config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
        config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
        
        logger.info(f"✅ Configuration loaded for {self.env.value}")
        
        return config
    
    def _get_database_url(self) -> str:
        """Holt Datenbank-URL basierend auf Umgebung"""
        if self.env == Environment.PRODUCTION:
            # Production sollte externe Datenbank verwenden
            url = os.getenv('DATABASE_URL')
            if not url:
                raise ValueError("DATABASE_URL not set in production environment")
            return url
        
        elif self.env == Environment.STAGING:
            return os.getenv('DATABASE_URL', 'sqlite:///staging.db')
        
        elif self.env == Environment.TESTING:
            return 'sqlite:///:memory:'
        
        else:  # DEVELOPMENT
            return os.getenv('DATABASE_URL', 'sqlite:///database.db')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Holt Konfigurationswert"""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Gibt alle Konfigurationswerte zurück"""
        return self.config.copy()


# ============================================================================
# Secrets Management
# ============================================================================

class SecretsManager:
    """Verwaltet Secrets und sensitive Daten"""
    
    def __init__(self):
        """Initialisiert SecretsManager"""
        self.secrets = self._load_secrets()
    
    def _load_secrets(self) -> Dict[str, str]:
        """Lädt Secrets aus Umgebung oder .secrets File"""
        secrets = {}
        
        # Aus Umgebungsvariablen
        sensitive_keys = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'EMAIL_PASSWORD',
            'OLLAMA_API_KEY',
            'API_TOKENS',
        ]
        
        for key in sensitive_keys:
            value = os.getenv(key)
            if value:
                secrets[key] = value
                logger.debug(f"✅ Loaded {key} from environment")
        
        # Aus .secrets Datei (für Development)
        secrets_file = Path('.secrets.json')
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    file_secrets = json.load(f)
                    secrets.update(file_secrets)
                    logger.info("✅ Loaded secrets from .secrets.json")
            
            except Exception as e:
                logger.warning(f"⚠️  Could not load .secrets.json: {e}")
        
        return secrets
    
    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """
        Holt Secret-Wert
        
        Args:
            key: Secret-Schlüssel
            default: Standardwert wenn nicht gefunden
        
        Returns:
            Secret-Wert oder Default
        
        Raises:
            ValueError: Wenn erforderlich und nicht gefunden
        """
        value = self.secrets.get(key, default)
        
        if value is None:
            logger.error(f"❌ Required secret not found: {key}")
            raise ValueError(f"Secret {key} not configured")
        
        return value
    
    def verify_required_secrets(self, required: list) -> bool:
        """
        Prüft ob alle erforderlichen Secrets vorhanden sind
        
        Args:
            required: Liste erforderlicher Secret-Keys
        
        Returns:
            True wenn alle vorhanden, False sonst
        """
        missing = [k for k in required if k not in self.secrets]
        
        if missing:
            logger.error(f"❌ Missing required secrets: {', '.join(missing)}")
            return False
        
        logger.info("✅ All required secrets present")
        return True


# ============================================================================
# Deployment Validation
# ============================================================================

class DeploymentValidator:
    """Validiert Deployment-Readiness"""
    
    @staticmethod
    def validate_production_deployment() -> Dict[str, bool]:
        """
        Validiert Production Deployment
        
        Returns:
            Dict mit Validierungsergebnissen
        """
        logger.info("🔍 Validating production deployment...")
        
        validation_results = {
            'environment': DeploymentValidator._check_environment(),
            'secrets': DeploymentValidator._check_secrets(),
            'database': DeploymentValidator._check_database(),
            'cache': DeploymentValidator._check_cache(),
            'security': DeploymentValidator._check_security(),
            'monitoring': DeploymentValidator._check_monitoring(),
        }
        
        all_passed = all(validation_results.values())
        
        if all_passed:
            logger.info("✅ Deployment validation PASSED")
        else:
            logger.error("❌ Deployment validation FAILED")
            failed = [k for k, v in validation_results.items() if not v]
            logger.error(f"   Failed checks: {', '.join(failed)}")
        
        return validation_results
    
    @staticmethod
    def _check_environment() -> bool:
        """Prüft Umgebung"""
        try:
            env = os.getenv('FLASK_ENV')
            if env not in ['production', 'staging', 'development']:
                logger.error(f"❌ Invalid FLASK_ENV: {env}")
                return False
            
            logger.info(f"✅ Environment: {env}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Environment check failed: {e}")
            return False
    
    @staticmethod
    def _check_secrets() -> bool:
        """Prüft Secrets"""
        try:
            secrets_manager = SecretsManager()
            required = ['SECRET_KEY', 'DATABASE_URL']
            
            if secrets_manager.verify_required_secrets(required):
                logger.info("✅ Secrets configured")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"❌ Secrets check failed: {e}")
            return False
    
    @staticmethod
    def _check_database() -> bool:
        """Prüft Datenbank"""
        try:
            from app.database import db
            from flask import current_app
            
            with current_app.app_context():
                db.session.execute("SELECT 1")
                logger.info("✅ Database connection OK")
                return True
        
        except Exception as e:
            logger.error(f"❌ Database check failed: {e}")
            return False
    
    @staticmethod
    def _check_cache() -> bool:
        """Prüft Cache (Redis)"""
        try:
            import redis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            
            logger.info("✅ Cache (Redis) OK")
            return True
        
        except Exception as e:
            logger.warning(f"⚠️  Cache check failed: {e}")
            return True  # Cache ist optional
    
    @staticmethod
    def _check_security() -> bool:
        """Prüft Security-Konfiguration"""
        try:
            secret_key = os.getenv('SECRET_KEY')
            
            if not secret_key or len(secret_key) < 32:
                logger.error("❌ SECRET_KEY too short or not set")
                return False
            
            logger.info("✅ Security configuration OK")
            return True
        
        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            return False
    
    @staticmethod
    def _check_monitoring() -> bool:
        """Prüft Monitoring"""
        try:
            # Versuche Prometheus zu laden
            import prometheus_client
            logger.info("✅ Monitoring (Prometheus) available")
            return True
        
        except ImportError:
            logger.warning("⚠️  Prometheus not available")
            return True  # Optional


# ============================================================================
# Configuration Builder
# ============================================================================

class ProductionConfigBuilder:
    """Erstellt Production-Konfiguration"""
    
    @staticmethod
    def build() -> Dict[str, Any]:
        """Erstellt vollständige Production-Konfiguration"""
        logger.info("🔨 Building production configuration...")
        
        config_manager = ConfigManager(Environment.PRODUCTION)
        secrets_manager = SecretsManager()
        
        # Basis-Konfiguration
        config = config_manager.get_all()
        
        # Database
        config['database'] = {
            'url': secrets_manager.get_secret('DATABASE_URL'),
            'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 40)),
        }
        
        # Cache
        config['cache'] = {
            'redis_url': secrets_manager.get_secret('REDIS_URL', 'redis://localhost:6379/0'),
            'default_ttl': int(os.getenv('CACHE_TTL', 3600)),
        }
        
        # Security
        config['security'] = {
            'secret_key': secrets_manager.get_secret('SECRET_KEY'),
            'allowed_origins': os.getenv('CORS_ALLOWED_ORIGINS', '*').split(','),
            'enable_csrf': True,
            'enable_rate_limiting': True,
        }
        
        # Monitoring
        config['monitoring'] = {
            'enable_metrics': True,
            'enable_logging': True,
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }
        
        logger.info("✅ Production configuration built successfully")
        
        return config


# ============================================================================
# Setup Function
# ============================================================================

def setup_configuration(app, env: Environment = None):
    """
    Initialisiert Konfiguration für Flask App
    
    Args:
        app: Flask Application
        env: Environment (auto-detected if not provided)
    """
    logger.info("⚙️  Setting up configuration...")
    
    config_manager = ConfigManager(env)
    app.config.update(config_manager.get_all())
    
    # Für Production: Validiere
    if config_manager.env == Environment.PRODUCTION:
        validation = DeploymentValidator.validate_production_deployment()
        if not all(validation.values()):
            raise RuntimeError("Production deployment validation failed")
    
    logger.info(f"✅ Configuration setup complete ({config_manager.env.value})")

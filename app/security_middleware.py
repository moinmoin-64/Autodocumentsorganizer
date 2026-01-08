"""
Security Middleware Module
Erweiterte Security Features für Production
"""

import logging
from functools import wraps
from typing import Optional, List, Dict
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import safe_str_cmp
import time

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Implementiert wichtige Security-Header"""
    
    @staticmethod
    def init_app(app: Flask):
        """Registriert Security-Headers in Flask-App"""
        
        @app.after_request
        def set_security_headers(response):
            """Setze Security-Header für jeden Response"""
            
            # Content Security Policy - Verhindert XSS
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            
            # X-Frame-Options - Verhindert Clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # X-Content-Type-Options - Verhindert MIME-Type Sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # X-XSS-Protection - Browser XSS Filter
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Strict-Transport-Security - Erzwingt HTTPS
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
            
            # Referrer-Policy - Kontrolliert Referrer-Info
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy - Kontrolliert Browser-Features
            response.headers['Permissions-Policy'] = (
                'geolocation=(), '
                'microphone=(), '
                'camera=(), '
                'payment=(), '
                'usb=(), '
                'magnetometer=(), '
                'gyroscope=(), '
                'accelerometer=()'
            )
            
            # CORS Headers (falls aktiviert)
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response


class RateLimiter:
    """Rate Limiting für API-Protection"""
    
    _limiter: Optional[Limiter] = None
    
    @classmethod
    def init_app(cls, app: Flask, storage_uri: str = 'memory://'):
        """
        Initialisiert Rate Limiter
        
        Args:
            app: Flask Application
            storage_uri: Storage URI für Rate-Limit Daten (memory:// oder redis://)
        """
        cls._limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=storage_uri,
            strategy="fixed-window",
            default_limits=["200 per day", "50 per hour"],
        )
        
        logger.info("[OK] Rate Limiter aktiviert")
    
    @classmethod
    def limit(cls, limit: str):
        """
        Decorator für Rate-Limiting
        
        Args:
            limit: Limit-String z.B. "100/hour"
            
        Returns:
            Decorator-Funktion
        """
        if cls._limiter is None:
            # Fallback wenn nicht initialisiert
            return lambda f: f
        
        return cls._limiter.limit(limit)


class InputValidator:
    """Validiert und säubert Benutzereingaben"""
    
    # Blacklist gefährlicher Zeichen
    DANGEROUS_CHARS = [';', '|', '&', '$', '`', '\n', '\r']
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Säubert String-Input
        
        Args:
            value: Input-String
            max_length: Maximale Länge
            
        Returns:
            Gesäuberter String
        """
        if not isinstance(value, str):
            return ""
        
        # Längenbegrenzung
        value = value[:max_length]
        
        # Entferne gefährliche Zeichen
        for char in InputValidator.DANGEROUS_CHARS:
            value = value.replace(char, '')
        
        # Entferne NULL-Bytes
        value = value.replace('\x00', '')
        
        return value.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validiert Email-Adresse"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validiert Dateinamen"""
        import re
        # Nur alphanumerisch, Punkte, Striche, Unterstriche
        pattern = r'^[a-zA-Z0-9._\-äöüßÄÖÜ\s]+$'
        return bool(re.match(pattern, filename)) and len(filename) <= 255
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validiert URLs"""
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(pattern, url)) and len(url) <= 2000


class APIKeyValidator:
    """Validiert API-Keys"""
    
    _valid_keys: Dict[str, Dict] = {}
    
    @classmethod
    def register_key(cls, key: str, name: str, permissions: List[str]):
        """
        Registriert einen API-Key
        
        Args:
            key: API-Key String
            name: Name des Keys
            permissions: Liste von Permissions
        """
        cls._valid_keys[key] = {
            'name': name,
            'permissions': permissions,
            'created_at': time.time(),
            'last_used': None,
        }
    
    @classmethod
    def validate_key(cls, key: str, required_permission: str = None) -> bool:
        """
        Validiert API-Key
        
        Args:
            key: API-Key zum Prüfen
            required_permission: Optional erforderliche Permission
            
        Returns:
            True wenn gültig, sonst False
        """
        if key not in cls._valid_keys:
            return False
        
        key_data = cls._valid_keys[key]
        
        if required_permission and required_permission not in key_data['permissions']:
            return False
        
        # Update last_used
        key_data['last_used'] = time.time()
        
        return True
    
    @classmethod
    def get_key_info(cls, key: str) -> Optional[Dict]:
        """Hole Key-Informationen"""
        return cls._valid_keys.get(key)


def require_api_key(f):
    """Decorator für API-Key-Validierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API-Key erforderlich'}), 401
        
        if not APIKeyValidator.validate_key(api_key):
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return jsonify({'error': 'Invalid API-Key'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json(f):
    """Decorator zur JSON-Validierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({'error': 'Content-Type: application/json erforderlich'}), 400
            
            try:
                request.get_json()
            except Exception as e:
                logger.warning(f"Invalid JSON in request: {e}")
                return jsonify({'error': 'Invalid JSON'}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def log_security_event(event_type: str, details: Dict = None):
    """
    Logged Security-Events
    
    Args:
        event_type: Typ des Security-Events
        details: Zusätzliche Details
    """
    log_entry = {
        'event_type': event_type,
        'timestamp': time.time(),
        'ip_address': get_remote_address(),
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        **(details or {})
    }
    
    logger.warning(f"[SECURITY] {event_type}: {log_entry}")


class SQLInjectionProtection:
    """Protection gegen SQL-Injection"""
    
    @staticmethod
    def check_input(value: str) -> bool:
        """Prüft auf verdächtige SQL-Patterns"""
        dangerous_patterns = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE',
            'UNION', 'SELECT', 'ALTER', 'EXEC',
            '--', '/*', '*/', 'xp_', 'sp_'
        ]
        
        value_upper = value.upper()
        
        for pattern in dangerous_patterns:
            if pattern in value_upper:
                return False
        
        return True


def init_security(app: Flask, config: Dict = None):
    """
    Initialisiert alle Security-Features
    
    Args:
        app: Flask Application
        config: Konfigurationsdictionary
    """
    config = config or {}
    
    # Security Headers
    SecurityHeadersMiddleware.init_app(app)
    logger.info("[OK] Security Headers aktiviert")
    
    # Rate Limiter
    storage_uri = config.get('rate_limit_storage', 'memory://')
    RateLimiter.init_app(app, storage_uri)
    logger.info("[OK] Rate Limiter aktiviert")
    
    # Security Event Logging
    logger.info("[OK] Security Event Logging aktiviert")

"""
Rate Limiting & Request Throttling
Protects against abuse and ensures fair resource usage
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from collections import defaultdict
import hashlib
import time

logger = logging.getLogger(__name__)


# ============================================================================
# Token Bucket Rate Limiter
# ============================================================================

class RateLimiterConfig:
    """Rate Limiter Konfiguration"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size


class TokenBucket:
    """Token Bucket für Rate Limiting"""
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_interval: float = 1.0
    ):
        """
        Initialisiert Token Bucket
        
        Args:
            capacity: Maximale Anzahl Token
            refill_rate: Tokens pro refill_interval
            refill_interval: Sekunden zwischen Refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_interval = refill_interval
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Versucht, Tokens zu konsumieren
        
        Returns:
            True wenn erfolgreich, False wenn nicht genug Tokens
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def _refill(self):
        """Füllt Tokens auf"""
        now = time.time()
        time_passed = now - self.last_refill
        
        if time_passed >= self.refill_interval:
            refills = int(time_passed / self.refill_interval)
            new_tokens = refills * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
    
    def get_remaining(self) -> int:
        """Gibt Anzahl verbleibender Tokens zurück"""
        self._refill()
        return int(self.tokens)


# ============================================================================
# Request Identifier
# ============================================================================

class RequestIdentifier:
    """Identifiziert Requester für Rate Limiting"""
    
    @staticmethod
    def get_client_id() -> str:
        """
        Ermittelt eindeutige Client-ID
        
        Priorität:
        1. User ID (falls authenticated)
        2. API Key
        3. IP Address
        """
        # Check for authenticated user
        if hasattr(g, 'user') and g.user:
            return f"user_{g.user.id}"
        
        # Check for API Key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Hash API Key für Privacy
            return f"api_{hashlib.sha256(api_key.encode()).hexdigest()[:8]}"
        
        # Fallback to IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        return request.remote_addr or 'unknown'
    
    @staticmethod
    def get_endpoint_id() -> str:
        """Gibt Endpoint-Identifikation zurück"""
        return f"{request.method}:{request.endpoint or 'unknown'}"


# ============================================================================
# Rate Limiter Storage
# ============================================================================

class RateLimiterStore:
    """Speichert Rate Limiter Buckets"""
    
    def __init__(self):
        """Initialisiert Store"""
        self._buckets: Dict[str, TokenBucket] = defaultdict(None)
        self._cleanup_interval = 3600  # 1 Stunde
        self._last_cleanup = time.time()
    
    def get_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float
    ) -> TokenBucket:
        """
        Holt oder erstellt Bucket
        
        Args:
            key: Eindeutiger Key für Bucket
            capacity: Token Capacity
            refill_rate: Refill Rate
        """
        self._cleanup_if_needed()
        
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(capacity, refill_rate)
        
        return self._buckets[key]
    
    def _cleanup_if_needed(self):
        """Bereinigt alte Buckets"""
        now = time.time()
        
        if now - self._last_cleanup >= self._cleanup_interval:
            # Entfernt Buckets die länger als 2 Stunden inaktiv sind
            cutoff_time = now - 7200
            expired_keys = [
                k for k, v in self._buckets.items()
                if v.last_refill < cutoff_time
            ]
            
            for key in expired_keys:
                del self._buckets[key]
            
            self._last_cleanup = now
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired rate limit buckets")


# Globale Instanz
rate_limiter_store = RateLimiterStore()


# ============================================================================
# Rate Limit Decorator
# ============================================================================

def rate_limit(
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    burst_size: Optional[int] = None
):
    """
    Rate Limiting Decorator
    
    Args:
        requests_per_minute: Requests pro Minute
        requests_per_hour: Requests pro Stunde
        burst_size: Maximale Burst Größe
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = RequestIdentifier.get_client_id()
            endpoint_id = RequestIdentifier.get_endpoint_id()
            
            # Per-Minute Check
            if requests_per_minute:
                minute_key = f"{client_id}:minute:{endpoint_id}"
                minute_bucket = rate_limiter_store.get_bucket(
                    minute_key,
                    requests_per_minute,
                    requests_per_minute / 60.0
                )
                
                if not minute_bucket.consume():
                    remaining = minute_bucket.get_remaining()
                    logger.warning(
                        f"⚠️  Rate limit exceeded (per-minute) for {client_id}"
                    )
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': 60,
                        'limit': requests_per_minute,
                        'remaining': remaining
                    }), 429
            
            # Per-Hour Check
            if requests_per_hour:
                hour_key = f"{client_id}:hour:{endpoint_id}"
                hour_bucket = rate_limiter_store.get_bucket(
                    hour_key,
                    requests_per_hour,
                    requests_per_hour / 3600.0
                )
                
                if not hour_bucket.consume():
                    remaining = hour_bucket.get_remaining()
                    logger.warning(
                        f"⚠️  Rate limit exceeded (per-hour) for {client_id}"
                    )
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': 3600,
                        'limit': requests_per_hour,
                        'remaining': remaining
                    }), 429
            
            # Call original function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# ============================================================================
# Endpoint-specific Rate Limits
# ============================================================================

class EndpointLimits:
    """Vordefinierte Limits für verschiedene Endpoints"""
    
    # Authentication
    LOGIN = RateLimiterConfig(requests_per_minute=5, requests_per_hour=50)
    REGISTER = RateLimiterConfig(requests_per_minute=3, requests_per_hour=20)
    PASSWORD_RESET = RateLimiterConfig(requests_per_minute=3, requests_per_hour=20)
    
    # API Operations
    LIST_DOCUMENTS = RateLimiterConfig(requests_per_minute=30, requests_per_hour=1000)
    UPLOAD_FILE = RateLimiterConfig(requests_per_minute=10, requests_per_hour=100)
    SEARCH = RateLimiterConfig(requests_per_minute=30, requests_per_hour=1000)
    
    # Email Operations
    SEND_EMAIL = RateLimiterConfig(requests_per_minute=5, requests_per_hour=100)
    FETCH_EMAILS = RateLimiterConfig(requests_per_minute=10, requests_per_hour=200)
    
    # Heavy Operations
    OCR_PROCESS = RateLimiterConfig(requests_per_minute=5, requests_per_hour=50)
    EXPORT_DOCUMENT = RateLimiterConfig(requests_per_minute=5, requests_per_hour=100)
    
    # Default
    DEFAULT = RateLimiterConfig(requests_per_minute=60, requests_per_hour=1000)


# ============================================================================
# Adaptive Rate Limiting
# ============================================================================

class AdaptiveRateLimiter:
    """Adaptive Rate Limiting basierend auf System-Load"""
    
    def __init__(self):
        self.system_load_factor = 1.0  # 1.0 = normal, < 1.0 = restrict, > 1.0 = relax
        self._last_check = time.time()
    
    def update_load_factor(self):
        """Aktualisiert Load Factor basierend auf System"""
        import psutil
        
        now = time.time()
        if now - self._last_check < 60:  # Update nur jede Minute
            return
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # Berechne Load Factor
        avg_load = (cpu_percent + memory_percent) / 200.0  # Normalisiere auf 0-1
        
        if avg_load > 0.8:
            self.system_load_factor = 0.5  # Halbiere Rate Limits
            logger.warning(f"⚠️  System load high ({avg_load:.1%}), reducing rate limits")
        elif avg_load > 0.6:
            self.system_load_factor = 0.75
        else:
            self.system_load_factor = 1.0
        
        self._last_check = now
    
    def adjust_limit(self, limit: int) -> int:
        """Passt Limit basierend auf Load an"""
        return int(limit * self.system_load_factor)


adaptive_limiter = AdaptiveRateLimiter()


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

def setup_rate_limiting(app):
    """Initialisiert Rate Limiting für App"""
    
    logger.info("🚦 Setting up rate limiting...")
    
    @app.before_request
    def check_rate_limits():
        """Prüft Rate Limits vor jedem Request"""
        
        # Update adaptive limits
        adaptive_limiter.update_load_factor()
        
        # Get client info
        client_id = RequestIdentifier.get_client_id()
        endpoint_id = RequestIdentifier.get_endpoint_id()
        
        # Bestimme Limits für Endpoint
        limits = EndpointLimits.DEFAULT
        
        if request.endpoint:
            endpoint_lower = request.endpoint.lower()
            
            if 'login' in endpoint_lower:
                limits = EndpointLimits.LOGIN
            elif 'register' in endpoint_lower:
                limits = EndpointLimits.REGISTER
            elif 'upload' in endpoint_lower:
                limits = EndpointLimits.UPLOAD_FILE
            elif 'search' in endpoint_lower:
                limits = EndpointLimits.SEARCH
            elif 'email' in endpoint_lower:
                limits = EndpointLimits.FETCH_EMAILS
        
        # Adjust limits based on system load
        adjusted_min = adaptive_limiter.adjust_limit(limits.requests_per_minute)
        adjusted_hour = adaptive_limiter.adjust_limit(limits.requests_per_hour)
        
        # Per-Minute Check
        minute_key = f"{client_id}:minute:{endpoint_id}"
        minute_bucket = rate_limiter_store.get_bucket(
            minute_key,
            adjusted_min,
            adjusted_min / 60.0
        )
        
        if not minute_bucket.consume():
            logger.warning(f"⚠️  Rate limit (minute) exceeded for {client_id}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': 60,
                'message': f'Maximum {adjusted_min} requests per minute'
            }), 429
        
        # Per-Hour Check
        hour_key = f"{client_id}:hour:{endpoint_id}"
        hour_bucket = rate_limiter_store.get_bucket(
            hour_key,
            adjusted_hour,
            adjusted_hour / 3600.0
        )
        
        if not hour_bucket.consume():
            logger.warning(f"⚠️  Rate limit (hour) exceeded for {client_id}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': 3600,
                'message': f'Maximum {adjusted_hour} requests per hour'
            }), 429
        
        # Add rate limit headers to g for response
        g.rate_limit_remaining_minute = minute_bucket.get_remaining()
        g.rate_limit_remaining_hour = hour_bucket.get_remaining()
    
    @app.after_request
    def add_rate_limit_headers(response):
        """Fügt Rate Limit Header zu Response hinzu"""
        if hasattr(g, 'rate_limit_remaining_minute'):
            response.headers['X-RateLimit-Remaining-Minute'] = str(g.rate_limit_remaining_minute)
        
        if hasattr(g, 'rate_limit_remaining_hour'):
            response.headers['X-RateLimit-Remaining-Hour'] = str(g.rate_limit_remaining_hour)
        
        return response
    
    logger.info("✅ Rate limiting setup complete")

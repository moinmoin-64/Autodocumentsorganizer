"""
Cache Manager - Redis Caching mit Fallback
"""

import logging
import json
import pickle
from typing import Any, Optional, Union
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Verwaltet Caching via Redis oder In-Memory (Fallback)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.redis = None
        self.enabled = False
        self._memory_cache = {}
        self._memory_cache_timestamps = {}  # Track insertion time
        
        try:
            import redis
            # Versuche Verbindung zu Redis
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=1,
                decode_responses=False  # Binary mode für pickle
            )
            self.redis.ping()
            self.enabled = True
            logger.info("Redis Cache verbunden")
        except (ImportError, redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis nicht verfügbar, nutze In-Memory Cache: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Redis-Setup: {e}")
            self.enabled = False
            
        self._initialized = True

    def get(self, key: str) -> Optional[Any]:
        """Holt Wert aus Cache"""
        try:
            if self.enabled and self.redis:
                data = self.redis.get(key)
                if data:
                    return pickle.loads(data)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache Get Error: {e}")
            return None
        return None

    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Setzt Wert im Cache (Default: 5 Min)"""
        try:
            if self.enabled and self.redis:
                data = pickle.dumps(value)
                return self.redis.setex(key, timeout, data)
            else:
                # Memory cache mit Timeout-Tracking
                import time
                self._memory_cache[key] = value
                self._memory_cache_timestamps[key] = time.time()
                
                # Cleanup alter Einträge (max 1000 items)
                if len(self._memory_cache) > 1000:
                    self._cleanup_memory_cache()
                
                return True
        except (pickle.PickleError, TypeError) as e:
            logger.error(f"Cache Serialization Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache Set Error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Löscht Wert aus Cache"""
        try:
            if self.enabled and self.redis:
                self.redis.delete(key)
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                if key in self._memory_cache_timestamps:
                    del self._memory_cache_timestamps[key]
            return True
        except Exception as e:
            logger.error(f"Cache Delete Error für key '{key}': {e}")
            return False
            
    def clear_pattern(self, pattern: str):
        """Löscht Keys nach Pattern (nur Redis)"""
        if self.enabled and self.redis:
            for key in self.redis.scan_iter(pattern):
                self.redis.delete(key)
        else:
            # Simple prefix match for memory cache
            keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(pattern.replace('*', ''))]
            for k in keys_to_delete:
                del self._memory_cache[k]

    @staticmethod
    def cached(timeout: int = 300, key_prefix: str = ''):
        """Decorator für Caching von Funktionsaufrufen"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache = CacheManager()
                
                # Generiere Cache Key
                arg_str = str(args) + str(kwargs)
                key_hash = hashlib.md5(arg_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
                
                # Prüfe Cache
                cached_val = cache.get(cache_key)
                if cached_val is not None:
                    return cached_val
                
                # Führe Funktion aus
                result = func(*args, **kwargs)
                
                # Speichere in Cache
                cache.set(cache_key, result, timeout)
                
                return result
            return wrapper
        return decorator

    def _cleanup_memory_cache(self, max_age: int = 300):
        """Entfernt alte Einträge aus Memory Cache"""
        import time
        current_time = time.time()
        
        # Lösche Einträge älter als max_age Sekunden
        keys_to_delete = [
            key for key, timestamp in self._memory_cache_timestamps.items()
            if current_time - timestamp > max_age
        ]
        
        for key in keys_to_delete:
            del self._memory_cache[key]
            del self._memory_cache_timestamps[key]
        
        logger.debug(f"Cleanup: {len(keys_to_delete)} alte Cache-Einträge entfernt")

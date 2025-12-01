"""
Redis Client Module
Handles connection to Redis for caching and message queueing.
Includes graceful fallback if Redis is not available.
"""
import redis
import logging
import json
from typing import Optional, Any, Union
import os

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        
        self._connect()
        self.initialized = True

    def _connect(self):
        """Establishes connection to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self.client.ping()
            self.enabled = True
            logger.info(f"✅ Redis connected at {self.host}:{self.port}")
        except redis.ConnectionError:
            self.enabled = False
            logger.warning(f"⚠️ Redis not available at {self.host}:{self.port}. Caching disabled.")
        except Exception as e:
            self.enabled = False
            logger.error(f"Redis connection error: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache"""
        if not self.enabled or not self.client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled or not self.client:
            return False
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
            
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete_pattern error: {e}")
            return 0

    def publish(self, channel: str, message: Any) -> bool:
        """Publish message to channel"""
        if not self.enabled or not self.client:
            return False
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            return self.client.publish(channel, message) > 0
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
            return False

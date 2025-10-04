"""
Redis client for storing and retrieving search results
"""
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

class RedisCache:
    def __init__(self):
        # Redis connection
        self.redis = None
        self.ttl_hours = 24  # Results expire after 24 hours

        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis = redis.from_url(redis_url)
            # Test connection
            self.redis.ping()
            print("✅ Redis cache connected successfully!")
        except Exception as e:
            print(f"⚠️ Redis cache connection failed: {e}. Results will not be cached.")
            self.redis = None

    def save_search_result(self, email: str, result_data: Dict[str, Any]) -> str:
        """
        Save search result to Redis and return the UUID
        """
        if not self.redis:
            raise Exception("Redis not available")

        result_id = str(uuid.uuid4())

        # Prepare data to store
        data = {
            "id": result_id,
            "email": email,
            "phones": result_data.get("phones", []),
            "total": result_data.get("total", 0),
            "source": result_data.get("source", ""),
            "configuration": result_data.get("configuration", {}),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=self.ttl_hours)).isoformat()
        }

        # Save to Redis with TTL
        key = f"search:{result_id}"
        self.redis.setex(key, self.ttl_hours * 3600, json.dumps(data))

        return result_id

    def get_search_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get search result from Redis by ID
        """
        if not self.redis:
            return None

        key = f"search:{result_id}"
        data = self.redis.get(key)

        if data:
            return json.loads(data)
        return None

    def delete_expired_results(self):
        """
        Clean up expired results (Redis handles TTL automatically, but this can be used for manual cleanup)
        """
        # Redis handles TTL automatically, so this is mostly for logging/stats
        pass

# Global instance
redis_cache = RedisCache()

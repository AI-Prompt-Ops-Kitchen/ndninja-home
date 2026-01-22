import redis
import uuid
import os
from typing import Optional

class SessionService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except:
            self.redis_client = None
        self.session_prefix = "session:"
        self.session_ttl = 86400

    def create_session(self, user_id: int) -> str:
        session_id = str(uuid.uuid4())
        if self.redis_client:
            key = f"{self.session_prefix}{session_id}"
            self.redis_client.setex(key, self.session_ttl, str(user_id))
        return session_id

    def get_session(self, session_id: str) -> Optional[int]:
        if not self.redis_client:
            return None
        key = f"{self.session_prefix}{session_id}"
        user_id = self.redis_client.get(key)
        return int(user_id) if user_id else None

    def delete_session(self, session_id: str) -> None:
        if self.redis_client:
            key = f"{self.session_prefix}{session_id}"
            self.redis_client.delete(key)

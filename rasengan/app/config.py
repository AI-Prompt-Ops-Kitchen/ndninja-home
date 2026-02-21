"""Rasengan configuration — all settings from environment variables."""

import os


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://rasengan_user:rasengan2026@localhost:5432/rasengan",
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://:8NsEZXThezZwCQe0nwjGMZErrWVLe666Yy4UMkFV6Z4=@localhost:6379/0")
RASENGAN_PORT = int(os.environ.get("RASENGAN_PORT", "8050"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Redis Streams
STREAM_KEY = "rasengan:events"
CONSUMER_GROUP = "rasengan-hub"
CONSUMER_NAME = "rasengan-worker-1"
STREAM_MAXLEN = 10_000

# Context resume
GIT_DIR = os.environ.get("GIT_DIR", "/home/ndninja")
SHARINGAN_INDEX = os.environ.get(
    "SHARINGAN_INDEX", "/home/ndninja/.sharingan/index.json"
)

"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from typing import Optional


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def _optional_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _optional_str(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


TOKEN: str = _required_env("TELEGRAM_TOKEN")
GROUP_CHAT_ID: int = int(_required_env("GROUP_CHAT_ID"))

REDIS_HOST: str = _optional_str("REDIS_HOST", "redis") or "redis"
REDIS_PORT: int = _optional_int("REDIS_PORT", 6379)
REDIS_DB: int = _optional_int("REDIS_DB", 0)

START_MESSAGE: Optional[str] = _optional_str("START_MESSAGE")
REPLY_MESSAGE: str = _optional_str(
    "REPLY_MESSAGE",
    "Give me some time to think. Soon I will return to you with an answer.",
) or "Give me some time to think. Soon I will return to you with an answer."

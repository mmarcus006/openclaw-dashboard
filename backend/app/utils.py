"""Shared utility functions."""

import os
from datetime import datetime, timezone

from slowapi import Limiter
from slowapi.util import get_remote_address


def now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.environ.get("TESTING") != "1",
)

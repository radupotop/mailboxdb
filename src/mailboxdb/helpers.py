import hashlib
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256sum(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()

import email
import hashlib
from datetime import datetime, timezone


def email_from_bytes(raw_email: bytes):
    return email.message_from_bytes(raw_email)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256sum(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()

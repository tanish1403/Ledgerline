"""Password hashing with bcrypt.

Why bcrypt: pre-built binary wheels on Windows, well-understood by interviewers,
and the work factor (rounds) is configurable so it can be increased as hardware improves.
Plain-text passwords are never stored, logged, or returned — only the hash.
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*.  The salt is embedded in the returned string."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True only when *plain* matches *hashed*.  Constant-time comparison."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())

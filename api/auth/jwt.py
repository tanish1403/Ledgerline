"""JWT creation and verification.

Why PyJWT: lightweight, no hidden transitive crypto deps, actively maintained.
The token carries sub (user id as string) and role so RBAC checks on every
request don't require a DB round-trip.  We still hit the DB on /me to get fresh data.
"""

from datetime import UTC, datetime, timedelta

import jwt

from api.config import settings


def create_token(user_id: int, role: str) -> str:
    """Encode a signed JWT that expires after jwt_expire_minutes."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and verify the token.  Raises jwt.PyJWTError on any failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

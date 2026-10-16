"""FastAPI dependencies shared across routers.

`require_role` is a factory: calling it returns a FastAPI dependency function.
Putting RBAC enforcement here means every router says exactly what role it needs
in one line — no scattered auth logic.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.auth.jwt import decode_token
from api.db.models import Role, User
from api.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _get_current_user(
    token: str = Depends(oauth2_scheme),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """Decode the Bearer token and load the matching user from the database."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*roles: Role):
    """Return a dependency that enforces the caller has one of *roles*.

    Why a closure: FastAPI resolves the returned function as a dependency, so we
    get full DI (DB session, token) while still parameterising by role.
    """

    def _check(current_user: User = Depends(_get_current_user)) -> User:  # noqa: B008
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check

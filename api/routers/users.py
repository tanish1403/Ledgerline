"""Users router: GET /me, GET /users.

/me is available to any authenticated user.
/users is admin-only — listing all users is a privileged operation.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from api.db.models import Role, User
from api.db.session import get_db
from api.deps import require_role

router = APIRouter(tags=["users"])


class UserOut(BaseModel):
    """Public user representation — hashed_password is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role
    is_active: bool


_all_roles = (Role.viewer, Role.analyst, Role.admin)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(require_role(*_all_roles))) -> User:  # noqa: B008
    """Return the authenticated user's own profile."""
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(require_role(Role.admin)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[User]:
    """Return all users.  Admin only."""
    return db.query(User).all()

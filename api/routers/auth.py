"""Auth router: POST /auth/token.

We follow the OAuth2 password flow so standard tools (Swagger UI, curl with -d)
work without any custom client code.  The form fields are username/password
(OAuth2 spec) even though internally we call it email.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.hashing import verify_password
from api.auth.jwt import create_token
from api.db.models import User
from api.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TokenOut:
    """Exchange email + password for a signed JWT.

    OAuth2PasswordRequestForm uses the field name *username* by spec;
    we treat it as the email address.
    """
    user = db.query(User).filter(User.email == form.username).first()

    # Deliberately vague error — don't reveal whether the email exists.
    bad_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise bad_creds
    if not verify_password(form.password, user.hashed_password):
        raise bad_creds
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(user.id, user.role.value)
    return TokenOut(access_token=token)

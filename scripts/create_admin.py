"""Create the first admin user from environment variables.

Run once against a freshly migrated database:
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secret python scripts/create_admin.py

Why a script instead of a migration: seed data is environment-specific;
migrations should only change schema, not inject credentials.
"""

import os
import sys

# Allow running from the repo root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.auth.hashing import hash_password
from api.db.models import Role, User
from api.db.session import SessionLocal

_MISSING = object()


def _require_env(name: str) -> str:
    value = os.environ.get(name, _MISSING)
    if value is _MISSING or not value:
        print(f"ERROR: environment variable {name} is required", file=sys.stderr)
        sys.exit(1)
    return value  # type: ignore[return-value]


def main() -> None:
    email = _require_env("ADMIN_EMAIL")
    password = _require_env("ADMIN_PASSWORD")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists (role={existing.role.value}). Nothing changed.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=Role.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin user {email} created (id={user.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Alembic environment — ties migrations to our SQLAlchemy models and settings.

Why override env.py: the default reads the URL from alembic.ini, which would mean
storing credentials there.  Instead we pull DATABASE_URL from the environment via
api.config.settings, keeping secrets out of version control.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from api.config import settings

# Import Base so Alembic's autogenerate sees all model metadata.
from api.db.models import Base

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Point autogenerate at our models.
target_metadata = Base.metadata

# Inject the runtime DATABASE_URL so we never store credentials in alembic.ini.
alembic_config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Run without a live connection — emits SQL to stdout.

    Useful for generating migration scripts to review before applying.
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run against a live database connection — the normal path."""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

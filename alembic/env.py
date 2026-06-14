"""Ambiente do Alembic.

Lê a URL do banco das settings da API e usa o metadata dos modelos ORM como
alvo, de modo que `--autogenerate` enxergue o schema atual.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from wealthlab_api import models  # noqa: F401 — importa para registrar as tabelas
from wealthlab_api.config import get_settings
from wealthlab_api.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL vinda das settings (permite override por WEALTHLAB_DB_URL).
config.set_main_option("sqlalchemy.url", get_settings().db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,  # SQLite: ALTERs via batch
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

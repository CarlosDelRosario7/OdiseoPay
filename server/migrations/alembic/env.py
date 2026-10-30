from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config import Config
from src.extensions import db
from src import models

config = context.config
config.set_main_option("sqlalchemy.url", Config.SQLALCHEMY_DATABASE_URI.replace("%", "%%"))

# `flask db` construye la ruta a migrations/alembic/alembic.ini, que no
# existe porque el ini real vive en server/alembic.ini. Alembic CLI sí lo
# encuentra. Solo cargamos logging si el archivo está disponible.
if config.config_file_name and Path(config.config_file_name).is_file():
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def run_migrations_offline():
    context.configure(url=Config.SQLALCHEMY_DATABASE_URI, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

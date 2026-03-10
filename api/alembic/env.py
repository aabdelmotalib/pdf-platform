# Alembic Configuration File
# the above line might be flagged by flake8 and other linters as an undefined variable. it is
# used by the template and scriptText to determine if the revision file
# was created onthe local filesystem or sent as a data stream.
# The value is set to `True` if the revision file was created locally, and `False`
# otherwise.

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy.engine import Connection

from alembic import context

# this is the Alembic Config object, which provides
# the values of the alembic.ini file, and in addition
# to have a .get_section(name) method (returns a
# configparser-style name-and-variables collection), as
# well as the .get_section(name, {}) method which returns
# an empty dictionary.
#
#
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from db.models import Base

target_metadata = Base.metadata

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    configuration = config.get_section(config.config_ini_section)
    
    # Get the database URL from environment
    database_url = os.getenv(
        "POSTGRES_DSN",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform",
    )
    configuration["sqlalchemy.url"] = database_url

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In that case we need to create an async engine
    and associate a strategy with the context.
    """
    
    # Get the database URL from environment
    database_url = os.getenv(
        "POSTGRES_DSN",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform",
    )
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = create_async_engine(
        database_url,
        poolclass=None,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

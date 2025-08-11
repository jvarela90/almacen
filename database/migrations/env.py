"""
Alembic Environment Configuration for AlmacénPro v2.0
SQLite-compatible migration environment
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Import configuration
from config.env_config import EnvironmentConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import database models for autogenerate support
try:
    from database.models import Base
    target_metadata = Base.metadata
except ImportError:
    # If models.py doesn't exist or doesn't have a Base, use None
    target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_database_url():
    """Get database URL from environment configuration"""
    db_config = EnvironmentConfig.get_database_config()
    
    if db_config['type'] == 'postgresql':
        return (f"postgresql://{db_config['username']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    else:
        # SQLite
        db_path = db_config['path']
        # Ensure absolute path
        if not os.path.isabs(db_path):
            db_path = os.path.join(str(project_root), db_path)
        return f"sqlite:///{db_path}"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite specific options
        render_as_batch=True,  # Required for SQLite ALTER TABLE operations
        compare_type=True,     # Compare column types
        compare_server_default=True  # Compare default values
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override the SQLalchemy URL in alembic config
    alembic_config = config.get_section(config.config_ini_section)
    alembic_config['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite specific options
            render_as_batch=True,  # Required for SQLite ALTER TABLE operations
            compare_type=True,     # Compare column types
            compare_server_default=True  # Compare default values
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
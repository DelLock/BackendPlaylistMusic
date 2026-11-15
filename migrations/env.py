from alembic import context

import models  #нужно, чтобы таблицы попали в Base.metadata
from database import DATABASE_URL, Base, engine

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata,
                      literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

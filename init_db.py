"""Создаёт схему базы из миграций. То же самое делает команда `alembic upgrade head`."""
from alembic import command
from alembic.config import Config


def init_db() -> None:
    command.upgrade(Config("alembic.ini"), "head")


if __name__ == "__main__":
    init_db()

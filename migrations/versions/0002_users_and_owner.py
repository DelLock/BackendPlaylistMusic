"""Таблица users и владелец плейлиста (playlists.owner_id)

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    # Старые плейлисты остаются без владельца (owner_id пустой), данные не теряются
    if op.get_bind().dialect.name == "sqlite":
        # SQLite умеет добавить столбец со ссылкой на другую таблицу без пересоздания таблицы
        op.execute("ALTER TABLE playlists ADD COLUMN owner_id INTEGER REFERENCES users (id) ON DELETE SET NULL")
    else:
        op.add_column("playlists", sa.Column("owner_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_playlists_owner_id_users", "playlists", "users", ["owner_id"], ["id"], ondelete="SET NULL"
        )
    # Индекс под проверку «чей плейлист» и выборки по владельцу
    op.create_index("ix_playlists_owner_id", "playlists", ["owner_id"])


def downgrade() -> None:
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if is_sqlite:
        # Для удаления столбца SQLite пересоздаёт таблицу playlists. При включённых внешних ключах
        # удаление старой таблицы каскадно стёрло бы треки, поэтому на это время ключи выключаем
        op.execute("PRAGMA foreign_keys=OFF")

    op.drop_index("ix_playlists_owner_id", table_name="playlists")
    with op.batch_alter_table("playlists") as batch_op:
        if not is_sqlite:
            batch_op.drop_constraint("fk_playlists_owner_id_users", type_="foreignkey")
        batch_op.drop_column("owner_id")
    op.drop_table("users")

    if is_sqlite:
        op.execute("PRAGMA foreign_keys=ON")

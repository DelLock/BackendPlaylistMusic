"""Таблицы playlists и tracks, индексы

Revision ID: 0001
Revises:
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
    )
    # Индекс под поиск и фильтрацию плейлистов по названию
    op.create_index("ix_playlists_name", "playlists", ["name"])

    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("playlist_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("artist", sa.String(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("playlist_id", "title", "artist", name="uq_tracks_playlist_title_artist"),
    )
    # Индекс под самый частый запрос: «все треки плейлиста N» и проверку дублей
    op.create_index("ix_tracks_playlist_id", "tracks", ["playlist_id"])


def downgrade() -> None:
    op.drop_index("ix_tracks_playlist_id", table_name="tracks")
    op.drop_table("tracks")
    op.drop_index("ix_playlists_name", table_name="playlists")
    op.drop_table("playlists")

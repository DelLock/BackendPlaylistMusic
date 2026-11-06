-- Справочная схема. Источник правды: миграции Alembic (migrations/versions).
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    author VARCHAR NOT NULL
);

CREATE INDEX ix_playlists_name ON playlists (name);

CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    artist VARCHAR NOT NULL,
    duration INTEGER NOT NULL,
    FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    CONSTRAINT uq_tracks_playlist_title_artist UNIQUE (playlist_id, title, artist)
);

CREATE INDEX ix_tracks_playlist_id ON tracks (playlist_id);

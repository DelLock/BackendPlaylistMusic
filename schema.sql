-- Справочная схема. Источник правды: миграции Alembic (migrations/versions).
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'user',
    CONSTRAINT uq_users_username UNIQUE (username)
);

CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    owner_id INTEGER REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_playlists_name ON playlists (name);
CREATE INDEX ix_playlists_owner_id ON playlists (owner_id);

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

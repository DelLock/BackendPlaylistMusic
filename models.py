from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base
from security import MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH, USERNAME_RE

ROLE_USER = "user"
ROLE_ADMIN = "admin"


# ---------- Таблицы базы ----------

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)  # bcrypt, сам пароль нигде не хранится
    role = Column(String, nullable=False, default=ROLE_USER, server_default=ROLE_USER)


class DBPlaylist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    # Кто создал плейлист. Ставит сервер. У старых записей, созданных до появления
    # пользователей, пусто: менять их может только админ
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    tracks = relationship(
        "DBTrack", back_populates="playlist",
        cascade="all, delete-orphan", order_by="DBTrack.id",
    )


class DBTrack(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        # Страховка от дублей на уровне базы (основная проверка с кодом 409 в роутере)
        UniqueConstraint("playlist_id", "title", "artist", name="uq_tracks_playlist_title_artist"),
    )

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)

    playlist = relationship("DBPlaylist", back_populates="tracks")


# ---------- Схемы запросов и ответов ----------

def _not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


class TrackBase(BaseModel):
    title: str = Field(..., min_length=1)
    artist: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0)

    _strip_title = field_validator("title", "artist")(_not_blank)


class TrackCreate(TrackBase):
    pass


class Track(TrackBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: int


class PlaylistBase(BaseModel):
    name: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)

    _strip_fields = field_validator("name", "author")(_not_blank)


class PlaylistCreate(PlaylistBase):
    pass


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None

    # Если поле прислали, оно не может быть пустым или null
    @field_validator("name", "author")
    @classmethod
    def _check(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return _not_blank(value)


class Playlist(PlaylistBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: Optional[int] = None
    tracks: List[Track] = []


class PlaylistStats(BaseModel):
    playlist_id: int
    name: str
    total_tracks: int
    total_duration: int
    avg_duration: float


# ---------- Пользователи ----------

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _check_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_RE.fullmatch(value):
            raise ValueError("must be 3-32 characters: letters, digits, '.', '_' or '-'")
        return value

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"must be at least {MIN_PASSWORD_LENGTH} characters")
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"must be at most {MAX_PASSWORD_BYTES} bytes")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str


class User(BaseModel):
    """Пользователь в ответах API. Поля password_hash здесь нет, поэтому он не утечёт."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # секунд

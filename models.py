from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


# ---------- Таблицы базы ----------

class DBPlaylist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)

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
    tracks: List[Track] = []


class PlaylistStats(BaseModel):
    playlist_id: int
    name: str
    total_tracks: int
    total_duration: int
    avg_duration: float

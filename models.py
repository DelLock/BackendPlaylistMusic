from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List
from database import Base

class DBPlaylist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)

    tracks = relationship("DBTrack", back_populates="playlist", cascade="all, delete-orphan")

class DBTrack(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, index=True, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)

    playlist = relationship("DBPlaylist", back_populates="tracks")


class TrackBase(BaseModel):
    title: str = Field(..., min_length=1)
    artist: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0)

class TrackCreate(TrackBase):
    pass

class Track(TrackBase):
    id: int
    playlist_id: int

    class Config:
        from_attributes = True

class PlaylistBase(BaseModel):
    name: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None

class Playlist(PlaylistBase):
    id: int
    tracks: List[Track] = []

    class Config:
        from_attributes = True

class PlaylistStats(BaseModel):
    playlist_id: int
    total_tracks: int
    total_duration: int
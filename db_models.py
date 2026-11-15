from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)

    playlists = relationship("PlaylistDB", back_populates="owner", cascade="all, delete-orphan")


class PlaylistDB(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    owner = relationship("UserDB", back_populates="playlists")
    tracks = relationship("TrackDB", back_populates="playlist", cascade="all, delete-orphan")


class TrackDB(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)

    playlist = relationship("PlaylistDB", back_populates="tracks")

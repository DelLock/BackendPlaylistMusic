
from pydantic import BaseModel
from typing import Optional

class PlaylistBase(BaseModel):
    name: str
    author: str

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None

class Playlist(PlaylistBase):
    id: int

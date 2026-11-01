from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    DBPlaylist, DBTrack,
    Playlist, PlaylistCreate, PlaylistUpdate,
    Track, TrackCreate, PlaylistStats
)

router = APIRouter()

@router.post("/api/playlists", response_model=Playlist, status_code=status.HTTP_201_CREATED)
@router.post("/api/items", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/items/", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_playlist(playlist: PlaylistCreate, db: Session = Depends(get_db)):
    if not playlist.name or not playlist.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
        
    db_playlist = DBPlaylist(name=playlist.name, author=playlist.author)
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return db_playlist


@router.get("/api/playlists", response_model=List[Playlist])
@router.get("/api/items", response_model=List[Playlist], include_in_schema=False)
@router.get("/api/items/", response_model=List[Playlist], include_in_schema=False)
@router.get("/api/", response_model=List[Playlist], include_in_schema=False)
@router.get("/api", response_model=List[Playlist], include_in_schema=False)
def get_playlists(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DBPlaylist)
    if name:
        query = query.filter(DBPlaylist.name.ilike(f"%{name}%"))
    return query.offset(offset).limit(limit).all()


@router.get("/api/playlists/{id}", response_model=Playlist)
@router.get("/api/items/{id}", response_model=Playlist, include_in_schema=False)
@router.get("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.get("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.get("/api//{id}", response_model=Playlist, include_in_schema=False)
def get_playlist(id: int, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@router.patch("/api/playlists/{id}", response_model=Playlist)
@router.patch("/api/items/{id}", response_model=Playlist, include_in_schema=False)
@router.patch("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.patch("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.patch("/api//{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/playlists/{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/items/{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api//{id}", response_model=Playlist, include_in_schema=False)
def update_playlist(id: int, playlist_update: PlaylistUpdate, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    update_data = playlist_update.dict(exclude_unset=True)
    if 'name' in update_data:
        if not update_data['name'] or not update_data['name'].strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        playlist.name = update_data['name']
        
    if 'author' in update_data:
        playlist.author = update_data['author']
        
    db.commit()
    db.refresh(playlist)
    return playlist


@router.delete("/api/playlists/{id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/api/items/{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/items//{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api//{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_playlist(id: int, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.delete(playlist)
    db.commit()


@router.post("/api/playlists/{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED)
@router.post("/api/items/{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/items//{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/items/{playlist_id}//tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/items//{playlist_id}//tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api//{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/{playlist_id}//tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api//{playlist_id}//tracks", response_model=Track, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def add_track_to_playlist(playlist_id: int, track_in: TrackCreate, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    existing_track = db.query(DBTrack).filter(
        DBTrack.playlist_id == playlist_id,
        DBTrack.title.ilike(track_in.title.strip()),
        DBTrack.artist.ilike(track_in.artist.strip())
    ).first()

    if existing_track:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track with the same title and artist already exists in this playlist"
        )

    db_track = DBTrack(
        playlist_id=playlist_id,
        title=track_in.title,
        artist=track_in.artist,
        duration=track_in.duration
    )
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track


@router.get("/api/playlists/{playlist_id}/tracks", response_model=List[Track])
@router.get("/api/items/{playlist_id}/tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api/items//{playlist_id}/tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api/items/{playlist_id}//tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api/items//{playlist_id}//tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api/{playlist_id}/tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api//{playlist_id}/tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api/{playlist_id}//tracks", response_model=List[Track], include_in_schema=False)
@router.get("/api//{playlist_id}//tracks", response_model=List[Track], include_in_schema=False)
def get_playlist_tracks(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist.tracks


@router.delete("/api/playlists/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/api/items/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/items//{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/items/{playlist_id}//tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/items//{playlist_id}//tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api//{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/{playlist_id}//tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api//{playlist_id}//tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_track(playlist_id: int, track_id: int, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    track = db.query(DBTrack).filter(DBTrack.id == track_id, DBTrack.playlist_id == playlist_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found in this playlist")
        
    db.delete(track)
    db.commit()


@router.get("/api/playlists/{playlist_id}/stats", response_model=PlaylistStats)
@router.get("/api/items/{playlist_id}/stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api/items//{playlist_id}/stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api/items/{playlist_id}//stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api/items//{playlist_id}//stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api/{playlist_id}/stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api//{playlist_id}/stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api/{playlist_id}//stats", response_model=PlaylistStats, include_in_schema=False)
@router.get("/api//{playlist_id}//stats", response_model=PlaylistStats, include_in_schema=False)
def get_playlist_stats(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    total_tracks = len(playlist.tracks)
    total_duration = sum(t.duration for t in playlist.tracks)
    
    return PlaylistStats(
        playlist_id=playlist_id,
        total_tracks=total_tracks,
        total_duration=total_duration
    )
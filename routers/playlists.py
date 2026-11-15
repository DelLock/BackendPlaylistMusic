from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from database import get_db
from dependencies import get_current_user, get_playlist_for_write, get_playlist_or_404
from models import (
    DBPlaylist, DBTrack, DBUser,
    Playlist, PlaylistCreate, PlaylistUpdate, PlaylistStats,
    Track, TrackCreate,
)

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


def _escape_like(text: str) -> str:
    """Символы % и _ в поиске должны быть обычными буквами, а не шаблоном."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _stats_query(db: Session):
    """Один запрос в базу: COUNT, SUM и AVG по трекам каждого плейлиста (GROUP BY)."""
    return (
        db.query(
            DBPlaylist.id.label("playlist_id"),
            DBPlaylist.name.label("name"),
            func.count(DBTrack.id).label("total_tracks"),
            func.coalesce(func.sum(DBTrack.duration), 0).label("total_duration"),
            func.coalesce(func.avg(DBTrack.duration), 0.0).label("avg_duration"),
        )
        .outerjoin(DBTrack, DBTrack.playlist_id == DBPlaylist.id)
        .group_by(DBPlaylist.id, DBPlaylist.name)
        .order_by(DBPlaylist.id)
    )


# ---------- Плейлисты ----------

@router.post("", response_model=Playlist, status_code=status.HTTP_201_CREATED)
def create_playlist(
    playlist: PlaylistCreate,
    user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # owner_id ставит сервер по тому, кто вошёл. Если клиент пришлёт owner_id в теле, он игнорируется
    db_playlist = DBPlaylist(name=playlist.name, author=playlist.author, owner_id=user.id)
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return db_playlist


@router.get("", response_model=List[Playlist])
def get_playlists(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: Optional[str] = None,        # поиск по названию без учёта регистра
    author: Optional[str] = None,   # фильтр по автору
    db: Session = Depends(get_db),
):
    query = db.query(DBPlaylist).options(selectinload(DBPlaylist.tracks))
    if q:
        pattern = f"%{_escape_like(q.strip().lower())}%"
        query = query.filter(func.lower(DBPlaylist.name).like(pattern, escape="\\"))
    if author is not None:
        query = query.filter(DBPlaylist.author == author)
    # Без сортировки страницы limit/offset могут пересекаться
    return query.order_by(DBPlaylist.id).offset(offset).limit(limit).all()


# Важно: /stats объявлен ДО /{playlist_id}, иначе слово "stats" примется за id
@router.get("/stats", response_model=List[PlaylistStats])
def get_all_stats(db: Session = Depends(get_db)):
    return _stats_query(db).all()


@router.get("/{playlist_id}", response_model=Playlist)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    return get_playlist_or_404(db, playlist_id)


@router.patch("/{playlist_id}", response_model=Playlist)
@router.put("/{playlist_id}", response_model=Playlist, include_in_schema=False)
def update_playlist(
    data: PlaylistUpdate,
    playlist: DBPlaylist = Depends(get_playlist_for_write),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(playlist, field, value)
    db.commit()
    db.refresh(playlist)
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(
    playlist: DBPlaylist = Depends(get_playlist_for_write),
    db: Session = Depends(get_db),
):
    db.delete(playlist)
    db.commit()


# ---------- Треки плейлиста ----------

@router.post("/{playlist_id}/tracks", response_model=Track, status_code=status.HTTP_201_CREATED)
def add_track(
    track_in: TrackCreate,
    playlist: DBPlaylist = Depends(get_playlist_for_write),
    db: Session = Depends(get_db),
):
    playlist_id = playlist.id

    duplicate = db.query(DBTrack.id).filter(
        DBTrack.playlist_id == playlist_id,
        func.lower(DBTrack.title) == track_in.title.lower(),
        func.lower(DBTrack.artist) == track_in.artist.lower(),
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track with the same title and artist already exists in this playlist",
        )

    db_track = DBTrack(
        playlist_id=playlist_id,
        title=track_in.title,
        artist=track_in.artist,
        duration=track_in.duration,
    )
    db.add(db_track)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track with the same title and artist already exists in this playlist",
        )
    db.refresh(db_track)
    return db_track


@router.get("/{playlist_id}/tracks", response_model=List[Track])
def get_tracks(playlist_id: int, db: Session = Depends(get_db)):
    playlist = get_playlist_or_404(db, playlist_id)
    return playlist.tracks


@router.delete("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_track(
    track_id: int,
    playlist: DBPlaylist = Depends(get_playlist_for_write),
    db: Session = Depends(get_db),
):
    track = db.query(DBTrack).filter(
        DBTrack.id == track_id, DBTrack.playlist_id == playlist.id
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found in this playlist")
    db.delete(track)
    db.commit()


@router.get("/{playlist_id}/stats", response_model=PlaylistStats)
def get_playlist_stats(playlist_id: int, db: Session = Depends(get_db)):
    get_playlist_or_404(db, playlist_id)
    return _stats_query(db).filter(DBPlaylist.id == playlist_id).one()

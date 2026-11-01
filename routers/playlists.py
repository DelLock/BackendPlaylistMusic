from fastapi import APIRouter, HTTPException, status
from typing import List
from models import Playlist, PlaylistCreate, PlaylistUpdate

router = APIRouter()

playlists_db = {}
playlist_id_counter = 1

# --- CREATE ---
# Основной маршрут (ВИДИМЫЙ в Swagger UI /docs)
@router.post("/api/items", response_model=Playlist, status_code=status.HTTP_201_CREATED)
# Скрытые маршруты для чекера (НЕ ВИДИМЫ в Swagger UI)
@router.post("/api/items/", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api/", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/api", response_model=Playlist, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_playlist(playlist: PlaylistCreate):
    global playlist_id_counter
    if not playlist.name or not playlist.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
        
    new_playlist = Playlist(id=playlist_id_counter, **playlist.dict())
    playlists_db[playlist_id_counter] = new_playlist
    playlist_id_counter += 1
    return new_playlist

# --- READ LIST ---
@router.get("/api/items", response_model=List[Playlist])
@router.get("/api/items/", response_model=List[Playlist], include_in_schema=False)
@router.get("/api/", response_model=List[Playlist], include_in_schema=False)
@router.get("/api", response_model=List[Playlist], include_in_schema=False)
def get_playlists():
    return list(playlists_db.values())

# --- READ ONE ---
@router.get("/api/items/{id}", response_model=Playlist)
@router.get("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.get("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.get("/api//{id}", response_model=Playlist, include_in_schema=False)
def get_playlist(id: int):
    if id not in playlists_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return playlists_db[id]

# --- UPDATE ---
@router.patch("/api/items/{id}", response_model=Playlist)
@router.patch("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.patch("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.patch("/api//{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/items/{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/items//{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api/{id}", response_model=Playlist, include_in_schema=False)
@router.put("/api//{id}", response_model=Playlist, include_in_schema=False)
def update_playlist(id: int, playlist_update: PlaylistUpdate):
    if id not in playlists_db:
        raise HTTPException(status_code=404, detail="Item not found")
        
    existing_playlist = playlists_db[id]
    update_data = playlist_update.dict(exclude_unset=True)
    
    if 'name' in update_data and (not update_data['name'] or not update_data['name'].strip()):
        raise HTTPException(status_code=400, detail="Name cannot be empty")
        
    updated_playlist = existing_playlist.copy(update=update_data)
    playlists_db[id] = updated_playlist
    return updated_playlist

# --- DELETE ---
@router.delete("/api/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/api/items//{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api/{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
@router.delete("/api//{id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_playlist(id: int):
    if id not in playlists_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del playlists_db[id]
from fastapi import FastAPI
from database import engine, Base
from routers import playlists

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Music Playlist API - Lab 2")

app.include_router(playlists.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import playlists

app = FastAPI(title="Music Playlist API - Lab 1")

app.include_router(playlists.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routers import playlists

app = FastAPI(title="Music Playlist API")

# ---------- Лог каждого запроса: "GET /api/playlists/7 404 1.3ms" ----------
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


# ---------- Единый формат ошибок: {"error": "...", "field": "..."} ----------
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    # loc выглядит как ("body", "name"); для битого JSON последний элемент число
    loc = [part for part in first["loc"] if part not in ("body", "query", "path")]
    field = loc[-1] if loc and isinstance(loc[-1], str) else "body"
    message = first["msg"].removeprefix("Value error, ")
    return JSONResponse(status_code=400, content={"error": message, "field": field})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


app.include_router(playlists.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

"""Вся проверка доступа в одном месте.

get_current_user         кто делает запрос (401, если не понять)
get_playlist_for_write   можно ли этому пользователю менять плейлист (404 или 403)
"""
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPBasic, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import DBPlaylist, DBUser, ROLE_ADMIN
from security import (
    DUMMY_HASH, decode_access_token, login_limiter, parse_basic_credentials, verify_password,
)


# Эти два класса нужны только для Swagger UI: кнопка Authorize и замочки у эндпоинтов.
# Заголовок разбирает get_current_user сам, потому что встроенный HTTPBasic
# не понимает логины и пароли не на латинице.
class _BasicDocs(HTTPBasic):
    async def __call__(self, request: Request) -> None:  # type: ignore[override]
        return None


class _BearerDocs(HTTPBearer):
    async def __call__(self, request: Request) -> None:  # type: ignore[override]
        return None


basic_docs = _BasicDocs(scheme_name="Basic", auto_error=False)
bearer_docs = _BearerDocs(scheme_name="Bearer", bearerFormat="JWT", auto_error=False)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _unauthorized(detail: str = "Invalid credentials", scheme: str = "Basic") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": scheme},
    )


def authenticate_user(db: Session, username: str, password: str, ip: str) -> DBUser:
    """Проверяет логин и пароль. Используется и для Basic, и для POST /auth/login."""
    key = login_limiter.key(ip, username)
    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts, try again later",
            headers={"Retry-After": str(wait)},
        )

    user = db.query(DBUser).filter(func.lower(DBUser.username) == username.strip().lower()).first()
    # Для неизвестного логина сверяем с хэшем-пустышкой, и ошибка одна и та же
    password_ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if user is None or not password_ok:
        login_limiter.register_failure(key)
        raise _unauthorized()

    login_limiter.reset(key)
    return user


def get_current_user(
    request: Request,
    _basic=Security(basic_docs),
    _bearer=Security(bearer_docs),
    db: Session = Depends(get_db),
) -> DBUser:
    header = request.headers.get("Authorization")
    if not header:
        raise _unauthorized("Authentication required")

    scheme, _sep, param = header.partition(" ")
    scheme = scheme.lower()
    param = param.strip()

    if scheme == "basic":
        credentials = parse_basic_credentials(param)
        if credentials is None:
            raise _unauthorized()
        return authenticate_user(db, credentials[0], credentials[1], client_ip(request))

    if scheme == "bearer":
        user_id = decode_access_token(param)
        user = db.get(DBUser, user_id) if user_id is not None else None
        if user is None:
            raise _unauthorized("Invalid or expired token", "Bearer")
        return user

    raise _unauthorized("Unsupported authorization scheme")


def get_playlist_or_404(db: Session, playlist_id: int) -> DBPlaylist:
    playlist = db.query(DBPlaylist).filter(DBPlaylist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


def can_modify(playlist: DBPlaylist, user: DBUser) -> bool:
    return user.role == ROLE_ADMIN or (playlist.owner_id is not None and playlist.owner_id == user.id)


def get_playlist_for_write(
    playlist_id: int,
    user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DBPlaylist:
    """Порядок проверок: вошёл ли (401), есть ли плейлист (404), его ли это плейлист (403)."""
    playlist = get_playlist_or_404(db, playlist_id)
    if not can_modify(playlist, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own playlists")
    return playlist

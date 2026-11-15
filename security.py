"""Пароли, JWT и лимит неудачных входов. Здесь нет ни FastAPI, ни базы: только логика."""
import base64
import binascii
import logging
import math
import os
import re
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional, Tuple

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("api")

# ---------- Пароли (bcrypt) ----------

MIN_PASSWORD_LENGTH = 6
# bcrypt смотрит только на первые 72 байта пароля, длиннее не принимаем
MAX_PASSWORD_BYTES = 72
# Стоимость хэша. 10 это нижняя рекомендованная граница, Basic Auth проверяет пароль на каждом запросе
BCRYPT_ROUNDS = 10


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except ValueError:
        return False


# Хэш-пустышка: для неизвестного логина всё равно считаем bcrypt, чтобы по времени ответа
# нельзя было понять, есть такой пользователь или нет
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# ---------- JWT ----------

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Секрета в коде нет. Если его забыли задать, берём случайный: сервис работает,
    # но после перезапуска все выданные токены перестают подходить
    JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning("JWT_SECRET не задан в окружении, использован случайный секрет на время работы процесса")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """Возвращает id пользователя или None, если токен подделан, просрочен или битый."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],  # алгоритм зафиксирован, "alg: none" не пройдёт
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


# ---------- Разбор заголовка Basic ----------

def parse_basic_credentials(param: str) -> Optional[Tuple[str, str]]:
    """Из base64-части заголовка `Authorization: Basic ...` достаёт (логин, пароль).

    Раскодируем как UTF-8, чтобы русские логины и пароли работали.
    """
    try:
        decoded = base64.b64decode(param, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    username, sep, password = decoded.partition(":")
    if not sep:
        return None
    return username, password


# ---------- Лимит неудачных входов ----------

USERNAME_RE = re.compile(r"[\w.\-]{3,32}")


class LoginLimiter:
    """Не больше `max_failures` неудачных входов за `window_seconds` секунд.

    Считаем отдельно для каждой пары (адрес клиента, логин): один подбирающий не может
    заблокировать вход всем остальным. Счётчики лежат в памяти процесса.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 60) -> None:
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def key(ip: str, username: str) -> str:
        return f"{ip}|{username.strip().lower()[:64]}"

    def _prune(self, attempts: Deque[float], now: float) -> None:
        while attempts and now - attempts[0] >= self.window:
            attempts.popleft()

    def retry_after(self, key: str) -> int:
        """0, если пробовать можно. Иначе сколько секунд подождать."""
        now = time.monotonic()
        with self._lock:
            attempts = self._failures.get(key)
            if not attempts:
                return 0
            self._prune(attempts, now)
            if not attempts:
                del self._failures[key]
                return 0
            if len(attempts) < self.max_failures:
                return 0
            return max(1, math.ceil(attempts[0] + self.window - now))

    def register_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._failures) > 10_000:
                self._purge(now)
            attempts = self._failures.setdefault(key, deque())
            self._prune(attempts, now)
            attempts.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()

    def _purge(self, now: float) -> None:
        for key in list(self._failures):
            attempts = self._failures[key]
            self._prune(attempts, now)
            if not attempts:
                del self._failures[key]


login_limiter = LoginLimiter(max_failures=5, window_seconds=60)

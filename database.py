import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Строка подключения берётся из окружения (файл .env), в коде паролей нет
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)

if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _sqlite_setup(dbapi_connection, _record):
        # По умолчанию SQLite не следит за внешними ключами, включаем
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        # Встроенный lower() в SQLite понимает только латиницу.
        # Подменяем своим, чтобы «Кино» и «кино» считались одним словом.
        dbapi_connection.create_function(
            "lower", 1, lambda s: s.lower() if isinstance(s, str) else s, deterministic=True
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

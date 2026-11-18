"""Сиды: заполняют базу тестовыми данными и создают администратора. Запуск: python seed.py"""
import os

from dotenv import load_dotenv

from database import SessionLocal
from models import DBPlaylist, DBTrack, DBUser, ROLE_ADMIN
from security import hash_password

load_dotenv()

SEED = [
    ("Rock Classics", "Denis", [("Bohemian Rhapsody", "Queen", 354), ("Radio Ga Ga", "Queen", 343)]),
    ("Chill Evening", "Anna", [("Weightless", "Marconi Union", 480), ("Intro", "The xx", 127)]),
    ("Русский рок", "Denis", [("Группа крови", "Кино", 286)]),
]


def ensure_admin(db):
    """Создаёт администратора из ADMIN_USERNAME и ADMIN_PASSWORD (файл .env). Повторный запуск ничего не меняет."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("ADMIN_PASSWORD не задан в окружении, администратор не создан")
        return None

    admin = db.query(DBUser).filter(DBUser.username == username).first()
    if admin:
        print(f"Пользователь {username} уже есть, администратор не менялся")
        return admin

    admin = DBUser(username=username, password_hash=hash_password(password), role=ROLE_ADMIN)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Создан администратор: {username}")
    return admin


def seed() -> None:
    db = SessionLocal()
    try:
        # Админ создаётся всегда, даже если плейлисты уже есть (например, база осталась от лабы 2)
        admin = ensure_admin(db)

        if db.query(DBPlaylist).count() > 0:
            print("База не пустая, тестовые плейлисты пропущены")
            return
        for name, author, tracks in SEED:
            playlist = DBPlaylist(name=name, author=author, owner_id=admin.id if admin else None)
            playlist.tracks = [DBTrack(title=t, artist=a, duration=d) for t, a, d in tracks]
            db.add(playlist)
        db.commit()
        print(f"Добавлено плейлистов: {len(SEED)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

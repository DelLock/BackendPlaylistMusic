"""Сиды: заполняет пустую базу тестовыми данными. Запуск: python seed.py"""
from database import SessionLocal
from models import DBPlaylist, DBTrack

SEED = [
    ("Rock Classics", "Denis", [("Bohemian Rhapsody", "Queen", 354), ("Radio Ga Ga", "Queen", 343)]),
    ("Chill Evening", "Anna", [("Weightless", "Marconi Union", 480), ("Intro", "The xx", 127)]),
    ("Русский рок", "Denis", [("Группа крови", "Кино", 286)]),
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(DBPlaylist).count() > 0:
            print("База не пустая, сиды пропущены")
            return
        for name, author, tracks in SEED:
            playlist = DBPlaylist(name=name, author=author)
            playlist.tracks = [DBTrack(title=t, artist=a, duration=d) for t, a, d in tracks]
            db.add(playlist)
        db.commit()
        print(f"Добавлено плейлистов: {len(SEED)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

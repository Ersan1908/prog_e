"""Демонстрационные данные: python -m app.seed. Все фильмы и рейтинги условные."""

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT, Base, build_engine
from app.models import Movie
from app.schemas import MovieWrite


def main():
    engine = build_engine()
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            if session.scalar(select(func.count(Movie.id))):
                print("База уже содержит фильмы: заполнение пропущено.")
                return
            data = json.loads(
                (PROJECT_ROOT / "examples" / "movies.json").read_text(encoding="utf-8")
            )
            session.add_all(Movie(**MovieWrite.model_validate(row).model_dump()) for row in data)
            session.commit()
            print(f"Добавлено фильмов: {len(data)}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

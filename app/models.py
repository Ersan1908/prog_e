"""ORM-модель и ограничения таблицы movies."""

from sqlalchemy import CheckConstraint, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1888 AND 2100", name="valid_year"),
        CheckConstraint("rating BETWEEN 0 AND 10", name="valid_rating"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 1000", name="valid_duration"),
        CheckConstraint("length(trim(title)) BETWEEN 1 AND 200", name="valid_title"),
        CheckConstraint("length(trim(director)) BETWEEN 1 AND 120", name="valid_director"),
        CheckConstraint("length(trim(genre)) BETWEEN 1 AND 60", name="valid_genre"),
        CheckConstraint("length(description) <= 3000", name="valid_description"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    director: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer, index=True)
    genre: Mapped[str] = mapped_column(String(60))
    rating: Mapped[float] = mapped_column(Float, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

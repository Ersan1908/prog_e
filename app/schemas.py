"""Pydantic-схемы запросов, ответов и параметров списка."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MovieWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)

    title: str = Field(min_length=1, max_length=200, examples=["Тестовый фильм"])
    director: str = Field(min_length=1, max_length=120, examples=["Иван Петров"])
    year: int = Field(ge=1888, le=2100, strict=True, examples=[2024])
    genre: str = Field(min_length=1, max_length=60, examples=["Драма"])
    rating: float = Field(ge=0, le=10, strict=True, examples=[8.2])
    duration_minutes: int = Field(ge=1, le=1000, strict=True, examples=[110])
    description: str | None = Field(default=None, max_length=3000)

    @field_validator("genre")
    @classmethod
    def normalize_genre(cls, value: str) -> str:
        return value.capitalize()


class MovieRead(MovieWrite):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MovieQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)

    q: str | None = Field(default=None, min_length=1, max_length=200, description="Часть названия")
    year: int | None = Field(default=None, ge=1888, le=2100)
    genre: str | None = Field(default=None, min_length=1, max_length=60)
    rating_min: float | None = Field(default=None, ge=0, le=10)
    rating_max: float | None = Field(default=None, ge=0, le=10)
    sort_by: Literal["id", "title", "year", "rating"] = "id"
    order: Literal["asc", "desc"] = "asc"
    page: int = Field(default=1, ge=1, le=1_000_000_000)
    page_size: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def check_rating_range(self):
        if self.rating_min is not None and self.rating_max is not None:
            if self.rating_min > self.rating_max:
                raise ValueError("rating_min не может быть больше rating_max")
        return self


class MoviePage(BaseModel):
    items: list[MovieRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class GenreStats(BaseModel):
    genre: str
    count: int
    average_rating: float


class MovieStats(BaseModel):
    total_movies: int
    average_rating: float | None
    earliest_year: int | None
    latest_year: int | None
    genres: list[GenreStats]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["sqlite"]


class ErrorResponse(BaseModel):
    detail: str

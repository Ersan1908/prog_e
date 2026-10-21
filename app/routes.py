"""Маршруты API: CRUD, выборка, справочник жанров и агрегаты."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Movie
from app.schemas import (
    ErrorResponse,
    GenreStats,
    HealthResponse,
    MoviePage,
    MovieQuery,
    MovieRead,
    MovieStats,
    MovieWrite,
)

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_session)]
MovieId = Annotated[int, Path(gt=0, le=2**63 - 1, description="Идентификатор фильма")]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Фильм не найден"}}


def find_movie(session: Session, movie_id: int) -> Movie:
    movie = session.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return movie


@router.get("/health", tags=["Сервис"], summary="Проверить API и соединение с БД")
def health(session: DatabaseSession) -> HealthResponse:
    session.execute(select(1)).scalar_one()
    return HealthResponse(status="ok", database="sqlite")


@router.get("/api/v1/movies", tags=["Фильмы"], summary="Получить список фильмов")
def list_movies(params: Annotated[MovieQuery, Query()], session: DatabaseSession) -> MoviePage:
    """Фильтры объединяются условием AND. Поиск учитывает кириллицу.

    Рейтинг задаётся включительным диапазоном. При равных значениях сортировки
    используется id по возрастанию, чтобы страницы имели стабильный порядок.
    """
    conditions = []
    if params.q is not None:
        conditions.append(func.casefold(Movie.title).contains(params.q.casefold(), autoescape=True))
    if params.year is not None:
        conditions.append(Movie.year == params.year)
    if params.genre is not None:
        conditions.append(func.casefold(Movie.genre) == params.genre.casefold())
    if params.rating_min is not None:
        conditions.append(Movie.rating >= params.rating_min)
    if params.rating_max is not None:
        conditions.append(Movie.rating <= params.rating_max)

    # Пользователь выбирает только ключ белого списка, а не SQL-выражение.
    sort_columns = {
        "id": Movie.id,
        "title": func.casefold(Movie.title),
        "year": Movie.year,
        "rating": Movie.rating,
    }
    column = sort_columns[params.sort_by]
    ordering = column.desc() if params.order == "desc" else column.asc()
    total = session.scalar(select(func.count(Movie.id)).where(*conditions)) or 0
    movies = session.scalars(
        select(Movie)
        .where(*conditions)
        .order_by(ordering, Movie.id.asc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).all()
    return MoviePage(
        items=[MovieRead.model_validate(movie) for movie in movies],
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=(total + params.page_size - 1) // params.page_size,
    )


@router.post(
    "/api/v1/movies",
    tags=["Фильмы"],
    status_code=status.HTTP_201_CREATED,
    response_model=MovieRead,
    summary="Добавить фильм",
)
def create_movie(payload: MovieWrite, response: Response, session: DatabaseSession) -> Movie:
    movie = Movie(**payload.model_dump())
    session.add(movie)
    session.commit()
    session.refresh(movie)
    response.headers["Location"] = f"/api/v1/movies/{movie.id}"
    return movie


# Статические пути объявлены до /movies/{movie_id}.
@router.get("/api/v1/movies/stats", tags=["Аналитика"], summary="Получить статистику фильмотеки")
def movie_stats(session: DatabaseSession) -> MovieStats:
    count, average, earliest, latest = session.execute(
        select(
            func.count(Movie.id), func.avg(Movie.rating), func.min(Movie.year), func.max(Movie.year)
        )
    ).one()
    groups = session.execute(
        select(Movie.genre, func.count(Movie.id), func.avg(Movie.rating))
        .group_by(Movie.genre)
        .order_by(func.casefold(Movie.genre))
    ).all()
    return MovieStats(
        total_movies=count,
        average_rating=round(average, 2) if average is not None else None,
        earliest_year=earliest,
        latest_year=latest,
        genres=[GenreStats(genre=g, count=c, average_rating=round(a, 2)) for g, c, a in groups],
    )


@router.get("/api/v1/genres", tags=["Аналитика"], summary="Получить список используемых жанров")
def list_genres(session: DatabaseSession) -> list[str]:
    return list(
        session.scalars(select(Movie.genre).distinct().order_by(func.casefold(Movie.genre)))
    )


@router.get(
    "/api/v1/movies/{movie_id}",
    tags=["Фильмы"],
    response_model=MovieRead,
    responses=NOT_FOUND,
    summary="Получить фильм по ID",
)
def read_movie(movie_id: MovieId, session: DatabaseSession) -> Movie:
    return find_movie(session, movie_id)


@router.put(
    "/api/v1/movies/{movie_id}",
    tags=["Фильмы"],
    response_model=MovieRead,
    responses=NOT_FOUND,
    summary="Полностью обновить фильм",
)
def replace_movie(movie_id: MovieId, payload: MovieWrite, session: DatabaseSession) -> Movie:
    """PUT заменяет все редактируемые поля. Пропущенное description станет null."""
    movie = find_movie(session, movie_id)
    for field, value in payload.model_dump().items():
        setattr(movie, field, value)
    session.commit()
    session.refresh(movie)
    return movie


@router.delete(
    "/api/v1/movies/{movie_id}",
    tags=["Фильмы"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить фильм",
)
def delete_movie(movie_id: MovieId, session: DatabaseSession) -> Response:
    session.delete(find_movie(session, movie_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.main import create_app
from app.models import Movie

URL = "/api/v1/movies"
MOVIE = {
    "title": "Орбита надежды",
    "director": "Иван Петров",
    "year": 2024,
    "genre": "Фантастика",
    "rating": 8.4,
    "duration_minutes": 125,
    "description": "Учебный пример",
}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as connection:
        yield connection


@pytest.fixture
def catalog(client):
    rows = [
        MOVIE,
        {**MOVIE, "title": "Тихий город", "year": 2023, "genre": "Драма", "rating": 7.6},
        {**MOVIE, "title": "Орбита памяти", "rating": 8.8},
        {**MOVIE, "title": "100%_кино", "year": 2023, "genre": "Драма", "rating": 8.8},
    ]
    for row in rows:
        assert client.post(URL, json=row).status_code == 201
    return rows


def test_full_crud(client):
    response = client.post(URL, json=MOVIE)
    assert response.status_code == 201
    movie_id = response.json()["id"]
    location = f"{URL}/{movie_id}"
    assert response.headers["Location"] == location
    assert client.get(location).json() == {**MOVIE, "id": movie_id}
    replacement = {**MOVIE, "title": "Новая орбита", "rating": 9.1}
    replacement.pop("description")
    response = client.put(location, json=replacement)
    assert response.status_code == 200
    assert response.json() == {**replacement, "description": None, "id": movie_id}
    assert client.get(location).json() == response.json()
    deleted = client.delete(location)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(location).status_code == 404
    assert client.get(URL).json()["total"] == 0


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_movie(client, method):
    kwargs = {"json": MOVIE} if method == "put" else {}
    response = getattr(client, method)(f"{URL}/999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Фильм не найден"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("title", "x" * 201),
        ("director", ""),
        ("director", "x" * 121),
        ("genre", " "),
        ("genre", "x" * 61),
        ("year", 1887),
        ("year", 2101),
        ("year", 2020.5),
        ("year", True),
        ("rating", -0.1),
        ("rating", 10.1),
        ("rating", "NaN"),
        ("rating", True),
        ("duration_minutes", 0),
        ("duration_minutes", 1001),
        ("duration_minutes", 1.5),
        ("description", "x" * 3001),
        ("unknown", "value"),
    ],
)
def test_invalid_payload_does_not_write(client, field, value):
    assert client.post(URL, json={**MOVIE, field: value}).status_code == 422
    assert client.get(URL).json()["total"] == 0


def test_missing_required_field_and_partial_put(client):
    assert client.post(URL, json={"title": "Один заголовок"}).status_code == 422
    movie_id = client.post(URL, json=MOVIE).json()["id"]
    assert client.put(f"{URL}/{movie_id}", json={"rating": 9}).status_code == 422
    assert client.get(f"{URL}/{movie_id}").json()["rating"] == 8.4


def test_string_normalization(client):
    response = client.post(URL, json={**MOVIE, "title": "  Орбита  ", "genre": " фАнТаСтИкА "})
    assert response.status_code == 201
    assert response.json()["title"] == "Орбита"
    assert response.json()["genre"] == "Фантастика"


@pytest.mark.parametrize(("year", "rating", "duration"), [(1888, 0, 1), (2100, 10, 1000)])
def test_inclusive_field_boundaries(client, year, rating, duration):
    response = client.post(
        URL, json={**MOVIE, "year": year, "rating": rating, "duration_minutes": duration}
    )
    assert response.status_code == 201


def test_combined_filters_and_case_insensitive_search(client, catalog):
    response = client.get(
        URL,
        params={
            "q": "оРбИтА",
            "year": 2024,
            "genre": "фАнТаСтИкА",
            "rating_min": 8.5,
            "rating_max": 8.8,
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Орбита памяти"


@pytest.mark.parametrize("q", ["%", "_", "100%_"])
def test_search_treats_like_wildcards_as_text(client, catalog, q):
    result = client.get(URL, params={"q": q}).json()
    assert result["total"] == 1
    assert result["items"][0]["title"] == "100%_кино"


def test_search_input_is_not_sql(client, catalog):
    assert client.get(URL, params={"q": "' OR 1=1 --"}).json()["total"] == 0
    assert client.get(URL).json()["total"] == 4


@pytest.mark.parametrize("sort_by", ["id", "title", "year", "rating"])
@pytest.mark.parametrize("order", ["asc", "desc"])
def test_sorting_and_stable_pagination(client, catalog, sort_by, order):
    params = {"sort_by": sort_by, "order": order, "page_size": 2}
    first = client.get(URL, params=params).json()
    second = client.get(URL, params={**params, "page": 2}).json()
    assert (first["total"], first["total_pages"]) == (4, 2)
    items = first["items"] + second["items"]
    values = [row[sort_by].casefold() if sort_by == "title" else row[sort_by] for row in items]
    assert values == sorted(values, reverse=order == "desc")
    assert len({row["id"] for row in items}) == 4
    if sort_by == "rating":
        assert [row["id"] for row in items if row["rating"] == 8.8] == [3, 4]


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": 10**30},
        {"page_size": 0},
        {"page_size": 101},
        {"sort_by": "rating; DROP TABLE movies"},
        {"order": "up"},
        {"rating_min": 9, "rating_max": 8},
        {"rating_min": -1},
        {"rating_max": 11},
        {"rating_min": "nan"},
        {"rating_max": "inf"},
        {"year": 1887},
        {"q": "   "},
        {"genre": " "},
        {"typo": "value"},
    ],
)
def test_invalid_query(client, params):
    assert client.get(URL, params=params).status_code == 422


@pytest.mark.parametrize("movie_id", ["0", "-1", "abc", str(10**30)])
def test_invalid_id(client, movie_id):
    assert client.get(f"{URL}/{movie_id}").status_code == 422


def test_empty_collection(client):
    assert client.get(URL).json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 10,
        "total_pages": 0,
    }
    assert client.get(f"{URL}/stats").json() == {
        "total_movies": 0,
        "average_rating": None,
        "earliest_year": None,
        "latest_year": None,
        "genres": [],
    }
    assert client.get("/api/v1/genres").json() == []


def test_out_of_range_page_and_no_match(client, catalog):
    page = client.get(URL, params={"page": 99, "page_size": 2}).json()
    assert page["items"] == [] and page["total"] == 4
    assert client.get(URL, params={"year": 1900}).json()["total"] == 0


def test_statistics_and_genres(client, catalog):
    assert client.get(f"{URL}/stats").json() == {
        "total_movies": 4,
        "average_rating": 8.4,
        "earliest_year": 2023,
        "latest_year": 2024,
        "genres": [
            {"genre": "Драма", "count": 2, "average_rating": 8.2},
            {"genre": "Фантастика", "count": 2, "average_rating": 8.6},
        ],
    }
    assert client.get("/api/v1/genres").json() == ["Драма", "Фантастика"]


def test_health_documentation_and_openapi(client):
    assert client.get("/health").json() == {"status": "ok", "database": "sqlite"}
    assert client.get("/", follow_redirects=False).headers["location"] == "/docs"
    assert "SwaggerUIBundle" in client.get("/docs").text
    assert "redoc" in client.get("/redoc").text
    schema = client.get("/openapi.json").json()
    operations = [
        method
        for path in schema["paths"].values()
        for method in path
        if method
        in {
            "get",
            "post",
            "put",
            "delete",
        }
    ]
    assert len(operations) == 8
    assert "201" in schema["paths"][URL]["post"]["responses"]
    assert "404" in schema["paths"][URL + "/{movie_id}"]["get"]["responses"]


def test_data_survives_application_restart(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'persistent.db'}"
    with TestClient(create_app(database_url)) as first:
        movie_id = first.post(URL, json=MOVIE).json()["id"]
    with TestClient(create_app(database_url)) as second:
        assert second.get(f"{URL}/{movie_id}").json()["title"] == MOVIE["title"]


def test_database_constraint_rejects_invalid_rating(client):
    with client.app.state.session_factory() as session:
        session.add(Movie(**{**MOVIE, "rating": 11}))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert list(session.scalars(select(Movie))) == []


def test_seed_is_repeatable(tmp_path):
    environment = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'seed.db'}"}
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-m", "app.seed"],
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout
    with TestClient(create_app(environment["DATABASE_URL"])) as connection:
        assert connection.get(URL).json()["total"] == 8

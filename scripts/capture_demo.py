"""Записать воспроизводимые примеры ответов и OpenAPI без изменения рабочей БД."""

import json
import platform
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.database import PROJECT_ROOT
from app.main import create_app


def main():
    output = PROJECT_ROOT / "docs"
    output.mkdir(exist_ok=True)
    rows = json.loads((PROJECT_ROOT / "examples" / "movies.json").read_text(encoding="utf-8"))
    results = []
    with TemporaryDirectory() as directory:
        with TestClient(create_app(f"sqlite:///{Path(directory) / 'demo.db'}")) as client:

            def record(method, path, **kwargs):
                response = client.request(method, path, **kwargs)
                results.append(
                    {
                        "method": method,
                        "path": path,
                        "request": kwargs.get("json"),
                        "status": response.status_code,
                        "response": response.json() if response.content else None,
                    }
                )
                return response

            record("GET", "/health")
            for row in rows:
                client.post("/api/v1/movies", json=row).raise_for_status()
            record(
                "GET",
                "/api/v1/movies?q=ОРБИТА&year=2024&rating_min=8&sort_by=rating&order=desc&page_size=2",
            )
            record("GET", "/api/v1/movies/stats")
            record("GET", "/api/v1/genres")
            new_movie = {**rows[0], "title": "Контрольный фильм"}
            created = record("POST", "/api/v1/movies", json=new_movie).json()
            path = f"/api/v1/movies/{created['id']}"
            record("GET", path)
            record("PUT", path, json={**new_movie, "rating": 9.0})
            record("DELETE", path)
            record("GET", path)
            record("POST", "/api/v1/movies", json={**new_movie, "rating": 11})
            schema = client.get("/openapi.json").json()
            (output / "openapi.json").write_text(
                json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    evidence = {
        "python": platform.python_version(),
        "versions": {
            name: version(name)
            for name in ["fastapi", "pydantic", "SQLAlchemy", "uvicorn", "pytest"]
        },
        "requests": results,
    }
    (output / "demo-results.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Сохранено примеров запросов: {len(results)}")


if __name__ == "__main__":
    main()

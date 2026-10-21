"""Точка входа: python -m uvicorn app.main:app --reload."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import sessionmaker

from app.database import Base, build_engine
from app.routes import router


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = build_engine(database_url)
        Base.metadata.create_all(engine)
        application.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="API фильмотеки",
        description=(
            "Лабораторная работа: разработка REST API. Вариант 5. "
            "CRUD фильмов, поиск по названию, фильтры по году, жанру и рейтингу, "
            "сортировка, пагинация и статистика. Все тела запросов и ответов используют JSON."
        ),
        version="1.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Фильмы", "description": "Управление фильмами"},
            {"name": "Аналитика", "description": "Статистика и справочник жанров"},
            {"name": "Сервис", "description": "Проверка работоспособности"},
        ],
    )
    application.include_router(router)

    @application.get("/", include_in_schema=False)
    def docs_redirect():
        return RedirectResponse("/docs")

    return application


app = create_app()

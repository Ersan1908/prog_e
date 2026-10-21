"""Точка входа: python -m uvicorn app.main:app --reload."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    origins = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173,http://localhost:4173",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
        expose_headers=["Location"],
    )
    application.include_router(router)

    @application.get("/", include_in_schema=False)
    def docs_redirect():
        return RedirectResponse("/docs")

    return application


app = create_app()

"""Сборка PDF-отчёта из описания проекта и сохранённых результатов проверок."""

import json
import os
from pathlib import Path
from xml.etree import ElementTree

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "pdf" / "report.pdf"
WIDTH = A4[0] - 4.5 * cm


def register_fonts():
    candidates = [
        (
            Path("/System/Library/Fonts/Supplemental"),
            "Times New Roman.ttf",
            "Times New Roman Bold.ttf",
            "Courier New.ttf",
        ),
        (
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
            "times.ttf",
            "timesbd.ttf",
            "cour.ttf",
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu"),
            "DejaVuSerif.ttf",
            "DejaVuSerif-Bold.ttf",
            "DejaVuSansMono.ttf",
        ),
    ]
    for directory, regular, bold, mono in candidates:
        if all((directory / name).exists() for name in (regular, bold, mono)):
            for label, name in [("Report", regular), ("ReportBold", bold), ("ReportMono", mono)]:
                pdfmetrics.registerFont(TTFont(label, str(directory / name)))
            pdfmetrics.registerFontFamily("Report", normal="Report", bold="ReportBold")
            return
    raise RuntimeError("Установите Times New Roman и Courier New либо DejaVu Serif / Sans Mono")


def main():
    register_fonts()
    evidence = json.loads((ROOT / "docs/demo-results.json").read_text(encoding="utf-8"))
    tests = ElementTree.parse(ROOT / "docs/test-results.xml").getroot().find("testsuite")
    count = int(tests.attrib["tests"])
    assert int(tests.attrib["failures"]) == 0 and int(tests.attrib["errors"]) == 0
    requests = evidence["requests"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    styles = {
        "body": ParagraphStyle(
            "body",
            fontName="Report",
            fontSize=13,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=9,
            firstLineIndent=21,
        ),
        "heading": ParagraphStyle(
            "heading", fontName="ReportBold", fontSize=15, leading=20, spaceAfter=14
        ),
        "small": ParagraphStyle("small", fontName="Report", fontSize=11, leading=14, spaceAfter=6),
        "cell": ParagraphStyle("cell", fontName="Report", fontSize=10.5, leading=13),
        "cellhead": ParagraphStyle(
            "cellhead", fontName="ReportBold", fontSize=10.5, leading=13, textColor=colors.white
        ),
        "center": ParagraphStyle(
            "center", fontName="Report", fontSize=14, leading=21, alignment=TA_CENTER, spaceAfter=9
        ),
        "title": ParagraphStyle(
            "title",
            fontName="ReportBold",
            fontSize=17,
            leading=25,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "right": ParagraphStyle(
            "right", fontName="Report", fontSize=14, leading=22, alignment=TA_RIGHT
        ),
        "code": ParagraphStyle(
            "code",
            fontName="ReportMono",
            fontSize=8.8,
            leading=12,
            alignment=TA_LEFT,
            backColor=colors.HexColor("#F2F4F6"),
            borderPadding=8,
            spaceAfter=12,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Report",
            fontSize=10.5,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
    }
    story = []

    def p(text, style="body"):
        story.append(Paragraph(text, styles[style]))

    def h(text):
        p(text, "heading")

    def code(text):
        story.append(Preformatted(text.strip("\n"), styles["code"]))

    def table(headers, rows, widths):
        cells = [[Paragraph(str(item), styles["cellhead"]) for item in headers]]
        cells.extend([[Paragraph(str(item), styles["cell"]) for item in row] for row in rows])
        result = Table(
            cells, colWidths=[WIDTH * fraction for fraction in widths], repeatRows=1, hAlign="LEFT"
        )
        result.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273D53")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F3F5F7")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B9C3CD")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.extend([result, Spacer(1, 12)])

    def page():
        story.append(PageBreak())

    # Титульный лист.
    p("МТУСИ", "title")
    p("Московский технический университет<br/>связи и информатики", "center")
    story.append(Spacer(1, 3.1 * cm))
    p("ОТЧЁТ ПО ЛАБОРАТОРНОЙ РАБОТЕ", "title")
    p("«Разработка REST API»", "title")
    p("Дисциплина: «Программная инженерия»", "center")
    p("Вариант 5. API фильмотеки", "center")
    story.append(Spacer(1, 2.5 * cm))
    p("Выполнил: студент группы БСТ-2556<br/>Новосельцев Алексей Сергеевич", "right")
    story.append(Spacer(1, 0.7 * cm))
    p("Проверил: _________________________", "right")
    story.append(Spacer(1, 3.2 * cm))
    p("Москва, 2026", "center")
    page()

    h("1. Цель работы и индивидуальное задание")
    p(
        "Цель работы - освоить разработку REST API на Python, применение HTTP-методов GET, POST, PUT и DELETE, маршрутизацию, сериализацию JSON и хранение данных в реляционной базе."
    )
    p(
        "Индивидуальное задание: вариант 5, API фильмотеки. Требуется вести учёт фильмов, выполнять поиск по названию и фильтрацию по году и рейтингу. Основная сущность проекта - фильм."
    )
    table(
        ["Требование", "Реализация в проекте"],
        [
            ("Python, веб-фреймворк", "Python 3.12, FastAPI"),
            ("Хранение в базе данных", "SQLite, ORM SQLAlchemy 2"),
            ("CRUD основной сущности", "POST, GET, PUT, DELETE для фильмов"),
            ("Не менее 7 эндпоинтов", "8 операций API, без учёта документации"),
            (
                "Поиск, фильтрация или агрегация",
                "Поиск по названию; год, рейтинг, жанр; статистика",
            ),
            ("Проверка ввода", "Pydantic, ограничения CHECK в SQLite"),
            (
                "Сортировка, пагинация или авторизация",
                "Сортировка по 4 полям и постраничная выдача",
            ),
            ("Документация", "Swagger UI, ReDoc и OpenAPI JSON"),
        ],
        [0.44, 0.56],
    )
    h("2. Краткие теоретические сведения")
    p(
        "REST описывает взаимодействие клиента и сервера через ресурсы с адресами URI. В данном проекте коллекция фильмов доступна по /api/v1/movies, отдельный фильм - по этому же пути с идентификатором. Каждый запрос содержит сведения, необходимые для его обработки."
    )
    p(
        "GET читает ресурс, POST создаёт, PUT полностью заменяет редактируемые поля существующего ресурса, DELETE удаляет. Состояние обработки передаётся HTTP-кодом, данные - в JSON. FastAPI формирует OpenAPI-схему на основе объявленных маршрутов и моделей [1]."
    )
    page()

    h("3. Архитектура и структура проекта")
    p(
        "Клиент обращается к FastAPI по HTTP. Pydantic проверяет параметры и тело запроса, обработчик выполняет запрос через SQLAlchemy, а SQLite сохраняет изменения. Ответ проверяется схемой и сериализуется в JSON."
    )
    code(
        "HTTP-клиент / Swagger UI\n          | запрос JSON\n          v\nFastAPI -> Pydantic -> SQLAlchemy Session -> SQLite\n          | ответ JSON и HTTP-код\n          v\n        Клиент"
    )
    table(
        ["Файл / каталог", "Назначение"],
        [
            ("app/main.py", "Создание FastAPI, жизненный цикл, подключение маршрутов"),
            ("app/database.py", "Движок SQLite, Base, сессия БД для запроса"),
            ("app/models.py", "ORM-модель Movie, индексы, CHECK-ограничения"),
            ("app/schemas.py", "Модели ввода и ответа, фильтры и валидация"),
            ("app/routes.py", "8 операций API и формирование SQL-запросов"),
            ("app/seed.py", "Заполнение пустой БД учебными данными"),
            ("tests/test_api.py", "Автоматические проверки на временных базах"),
            ("examples/", "Данные JSON и готовые HTTP-запросы"),
            ("docs/", "OpenAPI, ответы API, результаты pytest, снимок Swagger"),
            ("scripts/", "Запись демонстрационных ответов и сборка PDF"),
        ],
        [0.34, 0.66],
    )
    p(
        "Таблица создаётся при запуске приложения. Сессия открывается для HTTP-запроса и закрывается после его завершения. Изменяющие операции фиксируются через commit(). Файл data/movies.db сохраняется между запусками, поэтому состояние не зависит от памяти процесса [1, 3]."
    )
    p(
        "В репозиторий включены восемь вымышленных учебных фильмов. Их названия, режиссёры и рейтинги служат для демонстрации и не являются внешними справочными данными."
    )
    page()

    h("4. Модель данных и валидация")
    p(
        "Таблица movies содержит один фильм в каждой строке. Идентификатор формируется базой. Для года и рейтинга созданы индексы. Поля ORM описывают хранение, а схемы Pydantic - допустимый ввод и формат JSON [3, 4]."
    )
    table(
        ["Поле", "Тип в SQLite", "Ограничение / назначение"],
        [
            ("id", "INTEGER", "Первичный ключ"),
            ("title", "VARCHAR(200)", "Название, 1-200 символов"),
            ("director", "VARCHAR(120)", "Режиссёр, 1-120 символов"),
            ("year", "INTEGER", "Год выпуска, 1888-2100"),
            ("genre", "VARCHAR(60)", "Жанр, 1-60 символов"),
            ("rating", "FLOAT", "Учебный рейтинг, 0-10 включительно"),
            ("duration_minutes", "INTEGER", "Длительность, 1-1000 минут"),
            ("description", "TEXT, NULL", "Описание до 3000 символов, необязательное"),
        ],
        [0.30, 0.25, 0.45],
    )
    p(
        "Пробелы по краям строк удаляются до проверки длины. Жанры приводятся к единой записи: « дРАМА » преобразуется в «Драма». Пустые обязательные строки, неизвестные поля, неверные типы и значения вне диапазонов отклоняются с кодом 422."
    )
    code(
        'class MovieWrite(BaseModel):\n    model_config = ConfigDict(\n        str_strip_whitespace=True,\n        extra="forbid", allow_inf_nan=False\n    )\n    title: str = Field(min_length=1, max_length=200)\n    year: int = Field(ge=1888, le=2100, strict=True)\n    rating: float = Field(ge=0, le=10, strict=True)\n    duration_minutes: int = Field(ge=1, le=1000, strict=True)'
    )
    p(
        "Фрагмент показывает основные ограничения; полный набор полей находится в app/schemas.py. Числа JSON проверяются строго: строка «8.2» или true не заменяют числовой рейтинг. Минимальная граница рейтинга в фильтре не может превышать максимальную."
    )
    p(
        "Ограничения диапазонов и длины строк продублированы через CHECK. Это позволяет базе отклонять ошибочные значения и при обходе HTTP-валидации."
    )
    page()

    h("5. Маршруты и HTTP-коды")
    p(
        "Версия предметного API включена в URI: /api/v1. Ниже приведены восемь реализованных операций. Автоматические /docs, /redoc, /openapi.json и перенаправление с / в этот перечень не включены."
    )
    table(
        ["Метод", "Путь", "Результат", "Код"],
        [
            ("GET", "/health", "Проверка API и БД", "200"),
            ("GET", "/api/v1/movies", "Список фильмов с параметрами", "200"),
            ("POST", "/api/v1/movies", "Созданный фильм с id", "201"),
            ("GET", "/api/v1/movies/{movie_id}", "Один фильм", "200"),
            ("PUT", "/api/v1/movies/{movie_id}", "Полностью обновлённый фильм", "200"),
            ("DELETE", "/api/v1/movies/{movie_id}", "Пустое тело ответа", "204"),
            ("GET", "/api/v1/movies/stats", "Статистика всей базы", "200"),
            ("GET", "/api/v1/genres", "Список используемых жанров", "200"),
        ],
        [0.13, 0.41, 0.34, 0.12],
    )
    p(
        "После POST сервер возвращает объект с id и заголовок Location, указывающий путь к созданному ресурсу. PUT принимает все обязательные редактируемые поля; если description пропущен, описание становится null. DELETE возвращает 204 без тела."
    )
    p(
        "Если фильм отсутствует, GET, PUT и DELETE по его идентификатору возвращают 404 с сообщением «Фильм не найден». Некорректное тело, ID или параметры списка дают 422 с описанием поля ошибки."
    )
    code('{\n  "detail": "Фильм не найден"\n}')
    p(
        "Статический путь /movies/stats объявлен раньше динамического /movies/{movie_id}; слово stats поэтому не воспринимается как числовой ID. /health выполняет SELECT 1, проверяя фактическое соединение с базой."
    )
    p(
        "Статистика включает количество фильмов, средний рейтинг, минимальный и максимальный год, а также число фильмов и средний рейтинг по каждому жанру. Для пустой БД числовые агрегаты без значения возвращаются как null, количество равно нулю."
    )
    page()

    h("6. Поиск, фильтры, сортировка и пагинация")
    table(
        ["Параметр", "Правило"],
        [
            ("q", "Часть названия, 1-200 символов, без учёта регистра"),
            ("year", "Точный год в диапазоне 1888-2100"),
            ("genre", "Точное совпадение жанра без учёта регистра"),
            ("rating_min / rating_max", "Нижняя и верхняя границы рейтинга, 0-10 включительно"),
            ("sort_by", "id, title, year или rating; по умолчанию id"),
            ("order", "asc или desc; по умолчанию asc"),
            ("page", "Номер страницы от 1 до 1 000 000 000; по умолчанию 1"),
            ("page_size", "Размер страницы 1-100; по умолчанию 10"),
        ],
        [0.33, 0.67],
    )
    p(
        "Условия поиска и фильтрации объединяются через AND. Для кириллицы в SQLite зарегистрирована функция casefold(). Поиск использует параметризованное выражение contains(..., autoescape=True), поэтому символы % и _ считаются буквальными."
    )
    p(
        "Поле сортировки выбирается из белого списка. При равных значениях дополнительно применяется id по возрастанию. Смещение вычисляется как (page - 1) × page_size. Число страниц равно округлению total / page_size вверх."
    )
    code(
        "GET /api/v1/movies?q=ОРБИТА&year=2024&rating_min=8\n    &sort_by=rating&order=desc&page_size=2"
    )
    search = requests[1]["response"]
    table(
        ["Название в фактическом ответе", "Год", "Рейтинг"],
        [(row["title"], row["year"], row["rating"]) for row in search["items"]],
        [0.63, 0.18, 0.19],
    )
    p(
        f"Метаданные ответа: total={search['total']}, page={search['page']}, page_size={search['page_size']}, total_pages={search['total_pages']}. Два фильма найдены по заглавному запросу «ОРБИТА» и расположены по убыванию рейтинга."
    )
    p(
        "При отсутствии совпадений возвращаются пустой items и total_pages=0. Для страницы за пределами выборки items пуст, но total отражает фактическое число подходящих записей."
    )
    page()

    h("7. Реализация CRUD-операций")
    p(
        "Ниже показаны фрагменты app/routes.py. При создании Pydantic-модель преобразуется в словарь, из него строится ORM-объект. После фиксации транзакции refresh() получает значения, назначенные базой."
    )
    code(
        'def create_movie(payload, response, session):\n    movie = Movie(**payload.model_dump())\n    session.add(movie)\n    session.commit()\n    session.refresh(movie)\n    response.headers["Location"] = f"/api/v1/movies/{movie.id}"\n    return movie'
    )
    p(
        "Чтение выполняется через session.get(Movie, movie_id). Если объект не найден, обработчик возбуждает HTTPException с кодом 404. Для ответа используется схема MovieRead с поддержкой ORM-атрибутов."
    )
    code(
        "def replace_movie(movie_id, payload, session):\n    movie = find_movie(session, movie_id)\n    for field, value in payload.model_dump().items():\n        setattr(movie, field, value)\n    session.commit()\n    session.refresh(movie)\n    return movie\n\ndef delete_movie(movie_id, session):\n    session.delete(find_movie(session, movie_id))\n    session.commit()\n    return Response(status_code=204)"
    )
    p(
        "Для краткости в этих листингах опущены декораторы и аннотации типов; полный исполняемый код находится в проекте. Декораторы @router.post, @router.get, @router.put и @router.delete связывают функции с HTTP-методами и путями."
    )
    p(
        "Параметризованные SQL-запросы отделяют значения пользователя от структуры SQL. Выборка выполняется с LIMIT и OFFSET, поэтому API не выгружает всю коллекцию на каждую страницу."
    )
    page()

    h("8. Запуск приложения и документация")
    code(
        "python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements.txt\npython -m app.seed\npython -m uvicorn app.main:app --reload"
    )
    p(
        "Требуется Python 3.12+. Команды выполняются из папки проекта. В Windows активация: .venv\\Scripts\\activate. Swagger UI: http://127.0.0.1:8000/docs; ReDoc: /redoc; схема: /openapi.json.",
        "small",
    )
    image = Image(str(ROOT / "docs/screenshots/swagger.jpg"))
    image.drawWidth = WIDTH
    image.drawHeight = WIDTH * image.imageHeight / image.imageWidth
    story.append(image)
    p("Рисунок 1 - фактический вид Swagger UI с восемью операциями API", "caption")
    page()

    h("9. Практическая проверка запросов")
    p(
        "Примеры выполнены через TestClient на отдельной временной SQLite. Сначала загружены восемь учебных фильмов. Полные тела запросов и ответов сохранены в docs/demo-results.json; рабочая база при этом не изменяется."
    )
    table(
        ["Действие", "HTTP-код", "Наблюдаемый результат"],
        [
            ("GET /health", requests[0]["status"], "status=ok, database=sqlite"),
            ("GET со списком и фильтрами", requests[1]["status"], "2 фильма, рейтинг по убыванию"),
            (
                "POST контрольного фильма",
                requests[4]["status"],
                f"Назначен id={requests[4]['response']['id']}",
            ),
            ("GET созданного фильма", requests[5]["status"], "Возвращён созданный объект"),
            ("PUT контрольного фильма", requests[6]["status"], "Рейтинг изменён на 9.0"),
            ("DELETE контрольного фильма", requests[7]["status"], "Тело ответа отсутствует"),
            ("GET удалённого фильма", requests[8]["status"], "Фильм не найден"),
            ("POST с рейтингом 11", requests[9]["status"], "Ошибка поля body.rating"),
        ],
        [0.43, 0.16, 0.41],
    )
    p("Пример тела POST-запроса, использованного при проверке:")
    code(json.dumps(requests[4]["request"], ensure_ascii=False, indent=2))
    stats = requests[2]["response"]
    p(
        f"Для исходного набора статистика вернула {stats['total_movies']} фильмов, средний рейтинг {stats['average_rating']}, годы от {stats['earliest_year']} до {stats['latest_year']}. Агрегаты вычисляются в SQL с помощью COUNT, AVG, MIN, MAX и GROUP BY."
    )
    page()

    h("10. Автоматическое тестирование")
    p(
        f"Тестирование выполнено в Python {evidence['python']}. Версии основных пакетов: FastAPI {evidence['versions']['fastapi']}, Pydantic {evidence['versions']['pydantic']}, SQLAlchemy {evidence['versions']['SQLAlchemy']}, Uvicorn {evidence['versions']['uvicorn']}, pytest {evidence['versions']['pytest']}. Прямые зависимости зафиксированы в requirements-файлах."
    )
    code(
        "python -m pip install -r requirements-dev.txt\nruff check .\nruff format --check .\npython -m pytest --cov=app --cov-report=term-missing"
    )
    table(
        ["Группа проверок", "Что проверено"],
        [
            ("CRUD", "Создание, чтение, замена, удаление; Location и пустой ответ 204"),
            ("Валидация", "Типы, границы, пустые строки, лишние поля, неверные ID"),
            ("Поиск и фильтры", "Кириллица, регистр, AND, буквальные % и _, SQL-подобная строка"),
            (
                "Сортировка и страницы",
                "4 поля, оба направления, равные значения, отсутствие повторов",
            ),
            ("Агрегаты", "Среднее, диапазон лет, группы жанров, пустая коллекция"),
            ("Хранение", "Чтение после перезапуска приложения и CHECK в SQLite"),
            ("Документация", "Доступность Swagger, ReDoc и 8 операций в OpenAPI"),
            ("Демонстрационные данные", "Повторное заполнение не создаёт копий"),
        ],
        [0.31, 0.69],
    )
    p(
        f"Результат: <b>{count} тестов пройдено, ошибок и падений нет</b>. Покрытие исполняемых строк приложения без скрипта заполнения app.seed составило 99%: покрыто 187 из 188 строк. Проверки Ruff также завершились успешно."
    )
    p(
        "Тесты используют независимые временные файлы SQLite. Проверка сохранения данных закрывает первое приложение и открывает второе с тем же файлом БД. GitHub Actions настроен на выполнение проверок при push и pull request."
    )
    p(
        "Среда выводит одно предупреждение Starlette об устаревании HTTPX в TestClient. Оно не является ошибкой и не изменяет результаты. Фактический JUnit-отчёт находится в docs/test-results.xml.",
        "small",
    )
    page()

    h("11. Вывод")
    p(
        "Разработан работающий REST API фильмотеки для варианта 5. Реализованы все четыре CRUD-операции, поиск по названию, фильтрация по году и рейтингу, дополнительный фильтр жанра и агрегирование данных. API содержит восемь операций, проверяет входные данные и предоставляет сортировку и пагинацию."
    )
    p(
        "SQLite обеспечивает сохранение данных между запусками. ORM-модель отделена от схем ввода и вывода. Схемы Pydantic задают правила проверки и сериализации, а Swagger UI и ReDoc позволяют изучать контракт и выполнять запросы. Автоматические проверки подтвердили заявленное поведение."
    )
    p(
        "В ходе работы применены принципы маршрутизации, HTTP-методы и коды, параметризованные запросы к БД, обработка ошибок и документирование OpenAPI. Цель лабораторной работы достигнута."
    )
    h("12. Комплект сдачи")
    p(
        "В комплект входят исходный код Python, requirements-файлы, инструкция README, учебные данные, примеры HTTP-запросов, тесты, сохранённая спецификация OpenAPI, журнал демонстрационных ответов и настоящий PDF-отчёт."
    )
    p(
        'Репозиторий для размещения: <link href="https://github.com/Ersan1908/prog_e" color="#174E8A">github.com/Ersan1908/prog_e</link>.',
        "small",
    )
    p(
        "Учебный проект рассчитан на локальное использование. Авторизация не добавлялась: соответствующее дополнительное требование выполнено сортировкой и пагинацией. При изменении схемы в дальнейших версиях потребуется добавить миграции базы."
    )
    h("13. Использованные источники")
    sources = [
        (
            "1. FastAPI. SQL (Relational) Databases",
            "https://fastapi.tiangolo.com/tutorial/sql-databases/",
        ),
        ("2. FastAPI. Testing", "https://fastapi.tiangolo.com/tutorial/testing/"),
        ("3. SQLAlchemy 2.0. SQLite", "https://docs.sqlalchemy.org/en/20/dialects/sqlite.html"),
        ("4. Pydantic. Fields", "https://docs.pydantic.dev/latest/concepts/fields/"),
    ]
    for title, url in sources:
        p(f'{title}.<br/><link href="{url}" color="#174E8A">{url}</link>', "small")
    p("Дата обращения к электронным источникам: 21.10.2026.", "small")

    def footer(canvas, doc):
        if doc.page > 1:
            canvas.saveState()
            canvas.setFont("Report", 10)
            canvas.drawCentredString(A4[0] / 2, 1.15 * cm, str(doc.page))
            canvas.restoreState()

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Разработка REST API. Вариант 5. API фильмотеки",
        author="Новосельцев Алексей Сергеевич, БСТ-2556",
        subject="Лабораторная работа по программной инженерии, МТУСИ",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()

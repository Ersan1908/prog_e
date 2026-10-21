"""PDF-отчёт по лабораторной №2: React, REST API и CORS."""

import json
from pathlib import Path
from xml.etree import ElementTree

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
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

from scripts.build_report import register_fonts

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "lab2"
OUTPUT = ROOT / "output" / "pdf" / "lab2-report.pdf"
WIDTH = A4[0] - 4.5 * cm


def main():
    register_fonts()
    versions = json.loads((DOCS / "versions.json").read_text())
    browser = json.loads((DOCS / "browser-checks.json").read_text())
    coverage = json.loads((DOCS / "coverage.json").read_text())["totals"]

    def test_count(path):
        root = ElementTree.parse(path).getroot()
        cases = list(root.iter("testcase"))
        assert cases and not list(root.iter("failure")) and not list(root.iter("error"))
        return len(cases)

    backend_tests = test_count(DOCS / "backend-tests.xml")
    frontend_tests = test_count(DOCS / "frontend-tests.xml")
    assert all(check["result"] == "passed" for check in browser["checks"])
    story = []
    styles = {
        "body": ParagraphStyle(
            "body2",
            fontName="Report",
            fontSize=12.5,
            leading=17.5,
            alignment=TA_JUSTIFY,
            firstLineIndent=21,
            spaceAfter=9,
        ),
        "heading": ParagraphStyle(
            "heading2", fontName="ReportBold", fontSize=15, leading=20, spaceAfter=12
        ),
        "center": ParagraphStyle(
            "center2",
            fontName="Report",
            fontSize=14,
            leading=21,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "title": ParagraphStyle(
            "title2",
            fontName="ReportBold",
            fontSize=17,
            leading=25,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "right": ParagraphStyle(
            "right2", fontName="Report", fontSize=14, leading=22, alignment=TA_RIGHT
        ),
        "small": ParagraphStyle(
            "small2", fontName="Report", fontSize=10.5, leading=14.5, spaceAfter=7
        ),
        "cell": ParagraphStyle("cell2", fontName="Report", fontSize=10, leading=13),
        "cellhead": ParagraphStyle(
            "cellhead2", fontName="ReportBold", fontSize=10, leading=13, textColor=colors.white
        ),
        "code": ParagraphStyle(
            "code2", fontName="ReportMono", fontSize=8.5, leading=11.5, spaceAfter=12
        ),
        "caption": ParagraphStyle(
            "caption2",
            fontName="Report",
            fontSize=10.5,
            leading=15,
            alignment=TA_CENTER,
            spaceBefore=7,
            spaceAfter=6,
        ),
    }

    def p(text, style="body"):
        story.append(Paragraph(text, styles[style]))

    def h(text):
        p(text, "heading")

    def code(text):
        story.append(Preformatted(text.strip("\n"), styles["code"]))

    def page():
        story.append(PageBreak())

    def table(headers, rows, widths):
        data = [[Paragraph(str(cell), styles["cellhead"]) for cell in headers]]
        data += [[Paragraph(str(cell), styles["cell"]) for cell in row] for row in rows]
        result = Table(data, colWidths=[WIDTH * value for value in widths], repeatRows=1)
        result.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#354638")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F3F5ED")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C1CDB5")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.extend([result, Spacer(1, 12)])

    p("МТУСИ", "title")
    p("Московский технический университет<br/>связи и информатики", "center")
    story.append(Spacer(1, 2.7 * cm))
    p("ОТЧЁТ ПО ЛАБОРАТОРНОЙ РАБОТЕ №2", "title")
    p("«Интеграция REST API<br/>с фронтендом на React»", "title")
    p("Дисциплина: «Программная инженерия»", "center")
    p("Вариант 5. Фильмотека «Кадр»", "center")
    story.append(Spacer(1, 2.1 * cm))
    p("Выполнил: студент группы БСТ-2556<br/>Новосельцев Алексей Сергеевич", "right")
    story.append(Spacer(1, 0.7 * cm))
    p("Проверил: _________________________", "right")
    story.append(Spacer(1, 2.7 * cm))
    p("Москва, 2026", "center")
    page()

    h("1. Цель, задание и использованные средства")
    p(
        "Цель - освоить взаимодействие React-приложения с REST API из лабораторной №1: получать данные по HTTP, отображать их и выполнять создание, изменение и удаление записей на клиенте."
    )
    p(
        "Для варианта 5 разработана фильмотека «Кадр». Backend первой работы сохранён: FastAPI, SQLAlchemy и SQLite. В сервер добавлен CORSMiddleware. Данные отображаются карточками; запросы выполняются встроенным fetch."
    )
    table(
        ["Требование", "Выполнение"],
        [
            ("Готовое API работы №1", "Используется существующее приложение app/ и таблица movies"),
            (
                "React + axios или fetch",
                f"React {versions['react']}, fetch; сборка Vite {versions['vite']}",
            ),
            ("GET, POST, PUT, DELETE", "Список и детали; добавление; замена; удаление"),
            ("Не менее трёх экранов", "Коллекция, форма, поиск, детали - четыре экрана"),
            ("Поиск или фильтрация", "Название, год, жанр, диапазон рейтинга"),
            ("Корректный CORS", "Прямые запросы между портами 5173 и 8000, preflight"),
            ("Оформление", "CSS, адаптивная сетка, SVG-постеры и состояния интерфейса"),
            ("Документация", "README, маршруты, примеры fetch, фактические скриншоты"),
        ],
        [0.39, 0.61],
    )
    h("2. Структура проекта")
    table(
        ["Файл", "Назначение"],
        [
            ("frontend/src/main.jsx", "React root, StrictMode, BrowserRouter"),
            ("frontend/src/App.jsx", "Навигация, коллекция, поиск, форма, детали"),
            ("frontend/src/api.js", "fetch, обработка HTTP-ошибок, JSON, валидация"),
            ("frontend/src/components.jsx", "Карточки, поля, загрузка, диалог, SVG-постеры"),
            ("frontend/src/styles.css", "Цвета, типографика, сетки и медиазапросы"),
            ("frontend/tests/api.test.js", "Проверки клиентской логики"),
            ("app/main.py, tests/test_cors.py", "Настройка и проверки CORS"),
        ],
        [0.43, 0.57],
    )
    page()

    h("3. Экраны приложения и маршруты API")
    p(
        "Навигация реализована через React Router. Коллекция показывает данные API, статистику и быстрый поиск. Общая форма используется для добавления и редактирования. Поиск вынесен на отдельный экран; карточка фильма открывает все его поля."
    )
    table(
        ["Путь клиента", "Экран / назначение"],
        [
            ("/", "Коллекция: карточки, сортировка, страницы"),
            ("/movies/new", "Новая карточка, отправка POST"),
            ("/movies/:id/edit", "Заполненная форма, отправка PUT"),
            ("/search", "Название, год, жанр и диапазон рейтинга"),
            ("/movies/:id", "Детали, изменение и удаление"),
        ],
        [0.40, 0.60],
    )
    p(
        "Маршруты React относятся к клиентскому интерфейсу. Они обращаются к следующим серверным операциям по адресу http://127.0.0.1:8000:"
    )
    table(
        ["Метод", "Путь API", "Использование"],
        [
            ("GET", "/api/v1/movies", "Список и фильтры"),
            ("GET", "/api/v1/movies/{id}", "Детали и исходные поля формы"),
            ("POST", "/api/v1/movies", "Добавление, код 201"),
            ("PUT", "/api/v1/movies/{id}", "Полная замена, код 200"),
            ("DELETE", "/api/v1/movies/{id}", "Удаление, код 204 без JSON"),
            ("GET", "/api/v1/genres", "Варианты жанра в поиске"),
            ("GET", "/api/v1/movies/stats", "Число фильмов, среднее, жанры"),
            ("GET", "/health", "Состояние соединения"),
        ],
        [0.12, 0.44, 0.44],
    )
    p(
        "Параметры q, year, genre, rating_min, rating_max, sort_by, order и page сохраняются в URL. На главной странице запрашивается до 8 фильмов, на странице поиска - до 6. Сортировка и фильтрация выполняются сервером, а не только над уже загруженными карточками."
    )
    p(
        "При загрузке показан индикатор, при отсутствии совпадений - пояснение и сброс фильтров, при ошибке - сообщение и повтор запроса. Отсутствующий фильм обрабатывается как 404."
    )
    page()

    h("4. Взаимодействие через fetch и настройка CORS")
    p(
        "Общий клиент request() проверяет response.ok, возвращает JSON успешного ответа и передаёт ошибки форме. Для DELETE с кодом 204 JSON не читается. Числа формы преобразуются через Number(), пустое описание - в null. Примеры:"
    )
    code(
        "const query = new URLSearchParams({\n  q: 'ОРБИТА', year: '2024', rating_min: '8.5'\n});\nawait request(`/api/v1/movies?${query}`);\n\nconst film = {\n  title: 'Между кадрами', director: 'Анна Миронова',\n  year: 2024, genre: 'Драма', rating: 8.7,\n  duration_minutes: 115, description: null\n};\nconst created = await request('/api/v1/movies', {\n  method: 'POST', body: film\n});\nawait request(`/api/v1/movies/${created.id}`, {\n  method: 'PUT', body: { ...film, rating: 9.3 }\n});\nawait request(`/api/v1/movies/${created.id}`, {\n  method: 'DELETE'\n});"
    )
    p(
        "GET-запросы запускаются через useEffect. При смене пути или фильтров AbortController отменяет прежний запрос. Обработчики событий выполняют POST, PUT и DELETE; форма блокируется до завершения сохранения [1, 4]."
    )
    p(
        "Frontend на порту 5173 и API на порту 8000 имеют разные origin. Браузер проверяет разрешение сервера через CORS. Для JSON-запросов он может сначала отправить OPTIONS preflight. В Vite proxy не используется, поэтому проверено именно междоменное обращение [3]."
    )
    code(
        "application.add_middleware(\n    CORSMiddleware,\n    allow_origins=[\n        'http://127.0.0.1:5173', 'http://localhost:5173',\n        'http://127.0.0.1:4173', 'http://localhost:4173',\n    ],\n    allow_credentials=False,\n    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],\n    allow_headers=['Content-Type'],\n    expose_headers=['Location'],\n)"
    )
    p(
        "Разрешённые origin можно переопределить через CORS_ORIGINS. Адрес backend задаётся VITE_API_URL; значение по умолчанию - http://127.0.0.1:8000. При новом порту клиента нужно добавить его origin в серверную настройку.",
        "small",
    )
    page()

    h("5. Запуск и проверка приложения")
    p(
        "Требуются Python 3.12+ и Node.js 22.12+. Сначала из корня репозитория запускается backend, затем в отдельном терминале - frontend [2]."
    )
    code(
        "# Терминал 1: корень проекта\npython3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements.txt\npython -m app.seed\npython -m uvicorn app.main:app --reload\n\n# Терминал 2: корень проекта\nnpm install --global pnpm@11.25.0\ncd frontend\npnpm install --frozen-lockfile\npnpm dev\n\n# Проверка клиента и сборка\npnpm test\npnpm build"
    )
    p(
        "Интерфейс доступен по http://127.0.0.1:5173, Swagger UI - по http://127.0.0.1:8000/docs. В Windows окружение активируется командой .venv\\Scripts\\activate. pnpm preview показывает результат сборки на порту 4173."
    )
    table(
        ["Проверка", "Фактический результат"],
        [
            ("Backend: pytest", f"{backend_tests} теста пройдено, включая 7 проверок CORS"),
            (
                "Покрытие backend без seed",
                f"{coverage['covered_lines']} из {coverage['num_statements']} строк, около 99%",
            ),
            (
                "Клиент: Node test runner",
                f"{frontend_tests} тестов пройдено: fetch, ошибки, JSON, валидация",
            ),
            ("Сборка Vite", "pnpm build выполнен успешно"),
            (
                "Проверка в браузере",
                f"{len(browser['checks'])} сценариев выполнены вручную через интерфейс",
            ),
        ],
        [0.44, 0.56],
    )
    p(
        "В браузере создан фильм «Между кадрами» с id=9, рейтинг изменён с 8,7 на 9,3. Обновление страницы подтвердило сохранение. Отмена удаления оставила запись в коллекции; подтверждение удалило её, после чего детали показали 404. В исходной коллекции осталось 8 учебных фильмов."
    )
    p(
        "Поиск ОРБИТА + 2024 + Фантастика + рейтинг 8.5..10 вернул только «Орбита памяти». Проверены пустая форма, неверный диапазон, переход на вторую страницу, сортировка и отсутствие совпадений. Результаты сохранены в docs/lab2/; клиентские unit-тесты не подменяют отдельную проверку интерфейса."
    )
    page()

    screenshots = [
        (
            "6. Главная страница: коллекция",
            "collection.jpg",
            "Карточки получены из API. Сверху отображаются статистика, поиск, сортировка и переход к добавлению. Иллюстрации выполнены в SVG.",
            "Рисунок 1 - список фильмов и статистика",
        ),
        (
            "7. Форма добавления и редактирования",
            "form.jpg",
            "На экране добавления введены данные контрольного фильма. Та же форма по /movies/:id/edit загружает существующие значения и отправляет PUT.",
            "Рисунок 2 - заполненная форма добавления",
        ),
        (
            "8. Поиск и фильтрация",
            "search.jpg",
            "Одновременно применены поиск по названию, год, жанр и диапазон рейтинга. Сервер вернул один подходящий фильм; значения фильтров сохранены в URL.",
            "Рисунок 3 - результат комбинированного поиска",
        ),
        (
            "9. Страница деталей фильма",
            "details.jpg",
            "После POST открыт созданный фильм. Видны все поля, рейтинг и действия редактирования и удаления. Контрольная запись после проверки удалена.",
            "Рисунок 4 - подробная карточка фильма",
        ),
    ]
    for title, filename, description, caption in screenshots:
        h(title)
        p(description, "small")
        image = Image(str(DOCS / "screenshots" / filename))
        scale = min(WIDTH / image.imageWidth, (21.1 * cm) / image.imageHeight)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        image.hAlign = "CENTER"
        story.append(image)
        p(caption, "caption")
        page()

    h("10. Вывод")
    p(
        "Выполнена интеграция React-приложения с REST API фильмотеки из первой лабораторной работы. Реализованы получение и отображение данных, добавление, редактирование, подтверждаемое удаление, поиск и фильтрация. Минимальное требование к числу экранов выполнено: доступны коллекция, общая форма, поиск и детали."
    )
    p(
        "Клиент использует fetch, обрабатывает ошибки и состояния загрузки. Сервер разрешает обращения с origin frontend через CORSMiddleware; GET и изменяющие операции проверены при работе двух локальных серверов. Изменения сохраняются в SQLite и доступны после обновления страницы."
    )
    p(
        "Тесты backend и клиентской логики пройдены, сборка выполнена. Скриншоты получены из работающего приложения. Цель работы достигнута: освоено взаимодействие браузерного интерфейса с серверным REST API."
    )
    h("11. Комплект сдачи")
    p(
        "Исходный код находится в app/ и frontend/. Краткая документация со структурой, API-маршрутами, fetch-примерами и скриншотами - frontend/README.md. Проверки и иллюстрации - docs/lab2/. Отчёт второй работы сохранён отдельно: output/pdf/lab2-report.pdf."
    )
    p(
        'Репозиторий: <link href="https://github.com/Ersan1908/prog_e" color="#315A35">github.com/Ersan1908/prog_e</link>.',
        "small",
    )
    h("12. Источники")
    for title, url in [
        (
            "1. React. Synchronizing with Effects",
            "https://react.dev/learn/synchronizing-with-effects",
        ),
        ("2. Vite. Getting Started", "https://vite.dev/guide/"),
        ("3. FastAPI. CORS", "https://fastapi.tiangolo.com/tutorial/cors/"),
        (
            "4. MDN. Using the Fetch API",
            "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
        ),
    ]:
        p(f'{title}.<br/><link href="{url}" color="#315A35">{url}</link>', "small")
    p("Дата обращения: 21.10.2026.", "small")

    def footer(canvas, doc):
        if doc.page > 1:
            canvas.saveState()
            canvas.setFont("Report", 10)
            canvas.drawCentredString(A4[0] / 2, 1.15 * cm, str(doc.page))
            canvas.restoreState()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Лабораторная работа №2. Интеграция REST API с React. Фильмотека",
        author="Новосельцев Алексей Сергеевич, БСТ-2556",
        subject="Программная инженерия, МТУСИ",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()

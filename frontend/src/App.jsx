import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useOutletContext,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  moviePayload,
  movieQuery,
  request,
  validateFilters,
  validateMovie,
} from "./api.js";
import {
  DeleteDialog,
  EmptyState,
  ErrorPanel,
  Field,
  Icon,
  Loading,
  MovieCard,
  Pagination,
  Poster,
  useResource,
} from "./components.jsx";

const numberFormat = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 2,
});
const FILTER_KEYS = ["q", "year", "genre", "rating_min", "rating_max"];

function Layout() {
  const location = useLocation();
  const health = useResource("/health");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 5000);
    return () => clearTimeout(timer);
  }, [notice]);
  const pageName =
    location.pathname === "/"
      ? "Коллекция"
      : location.pathname === "/search"
        ? "Поиск и фильтры"
        : location.pathname === "/movies/new"
          ? "Добавление фильма"
          : location.pathname.endsWith("/edit")
            ? "Редактирование"
            : "О фильме";
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Link className="brand" to="/" aria-label="Кадр - на главную">
          <span className="brand-mark">к</span>
          <span>
            кадр<span className="brand-sub">ЛИЧНАЯ ФИЛЬМОТЕКА</span>
          </span>
        </Link>
        <div className="nav-label">ВАШЕ ПРОСТРАНСТВО</div>
        <nav className="main-nav" aria-label="Главная навигация">
          <NavLink
            end
            to="/"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <Icon name="grid" />
            Коллекция
          </NavLink>
          <NavLink
            to="/search"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <Icon name="search" />
            Поиск и фильтры
          </NavLink>
          <NavLink
            to="/movies/new"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <Icon name="plus" />
            Добавить фильм
          </NavLink>
        </nav>
        <div className="sidebar-note">
          <Icon name="film" size={27} />
          <p>
            Хорошее кино
            <br />
            остаётся с вами.
          </p>
          <span>Соберите его здесь.</span>
        </div>
        <button
          className="connection"
          onClick={health.reload}
          title="Проверить соединение с сервером"
        >
          <span
            className={`status-dot${health.error ? " offline" : health.loading ? " pending" : ""}`}
          />
          {health.error
            ? "Сервер недоступен"
            : health.loading
              ? "Подключаемся…"
              : "Коллекция синхронизирована"}
        </button>
        <div className="sidebar-bottom">
          СОХРАНЯЙТЕ ИСТОРИИ <span>↗</span>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Моя фильмотека</span>
            <Icon name="chevron" size={13} />
            <span>{pageName}</span>
          </div>
          <span className="edition">
            КИНО В ДЕТАЛЯХ <span className="edition-dot" />
          </span>
        </header>
        <main id="main-content">
          <Outlet context={{ notify: setNotice }} />
        </main>
        <footer className="site-footer">
          <span>КАДР / ЛИЧНАЯ КОЛЛЕКЦИЯ</span>
          <span>Каждому фильму - своё место.</span>
        </footer>
      </div>
      {notice && (
        <div className="toast" role="status">
          <span className="toast-icon">
            <Icon name="check" size={17} />
          </span>
          {notice}
          <button
            className="icon-button"
            aria-label="Закрыть уведомление"
            onClick={() => setNotice("")}
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

function SortControl({ params, setParams }) {
  return (
    <label className="sort-control">
      <span>Сортировать</span>
      <select
        aria-label="Сортировка фильмов"
        value={`${params.get("sort_by") || "id"}:${params.get("order") || "asc"}`}
        onChange={(event) => {
          const [sort_by, order] = event.target.value.split(":");
          const next = new URLSearchParams(params);
          next.set("sort_by", sort_by);
          next.set("order", order);
          next.delete("page");
          setParams(next);
        }}
      >
        <option value="id:asc">По добавлению</option>
        <option value="rating:desc">По рейтингу ↓</option>
        <option value="year:desc">Сначала новые</option>
        <option value="title:asc">По названию А-Я</option>
      </select>
    </label>
  );
}

function Collection() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [revision, setRevision] = useState(0);
  const [deleting, setDeleting] = useState(null);
  const { notify } = useOutletContext();
  const movies = useResource(`/api/v1/movies?${movieQuery(params)}`, revision);
  const stats = useResource("/api/v1/movies/stats", revision);
  useEffect(() => {
    setQuery(params.get("q") || "");
  }, [params]);
  function goPage(page) {
    const next = new URLSearchParams(params);
    next.set("page", page);
    setParams(next);
  }
  function reset() {
    setQuery("");
    setParams({});
  }
  function onDeleted() {
    setDeleting(null);
    notify("Фильм удалён из коллекции");
    if (movies.data?.items.length === 1 && movies.data.page > 1)
      goPage(movies.data.page - 1);
    setRevision((value) => value + 1);
  }
  return (
    <div className="page collection-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow section-kicker">
            <span />
            ВАША ЛИЧНАЯ ПОДБОРКА
          </p>
          <h1>
            Коллекция фильмов<span className="title-dot">.</span>
          </h1>
          <p className="page-description">
            Истории, к которым хочется возвращаться.
          </p>
        </div>
        <Link className="button" to="/movies/new">
          <Icon name="plus" size={18} />
          Добавить фильм
        </Link>
      </div>
      <section className="collection-stats" aria-label="Статистика коллекции">
        <div>
          <span className="stat-number">
            {stats.data
              ? String(stats.data.total_movies).padStart(2, "0")
              : "—"}
          </span>
          <span className="stat-label">фильмов в коллекции</span>
        </div>
        <div>
          <span className="stat-number">
            {stats.data?.average_rating != null
              ? numberFormat.format(stats.data.average_rating)
              : "—"}
            <Icon name="star" size={21} />
          </span>
          <span className="stat-label">средний рейтинг</span>
        </div>
        <div>
          <span className="stat-number">
            {stats.data
              ? String(stats.data.genres.length).padStart(2, "0")
              : "—"}
          </span>
          <span className="stat-label">жанров для открытия</span>
        </div>
        <p className="stats-note">
          У каждого фильма
          <br />
          своя история.
          <br />
          <strong>Какая следующая?</strong>
        </p>
      </section>
      {stats.error && (
        <p className="inline-warning" role="alert">
          Не удалось получить статистику.{" "}
          <button className="text-button" onClick={stats.reload}>
            Повторить
          </button>
        </p>
      )}
      <div className="collection-toolbar">
        <form
          className="quick-search"
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            const next = new URLSearchParams(params);
            if (query.trim()) next.set("q", query.trim());
            else next.delete("q");
            next.delete("page");
            setParams(next);
          }}
        >
          <Icon name="search" size={19} />
          <input
            aria-label="Поиск по названию"
            placeholder="Найти фильм по названию…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            maxLength={200}
          />
          {query && (
            <button
              type="button"
              className="icon-button"
              aria-label="Очистить поиск"
              onClick={reset}
            >
              <Icon name="close" size={15} />
            </button>
          )}
          <button className="search-submit" aria-label="Найти фильм">
            <Icon name="arrow" size={18} />
          </button>
        </form>
        <div className="toolbar-actions">
          <Link
            className="filter-link"
            to={`/search${params.toString() ? `?${params}` : ""}`}
          >
            <Icon name="filter" size={17} />
            Фильтры
          </Link>
          <SortControl params={params} setParams={setParams} />
        </div>
      </div>
      <div className="results-caption">
        <span>
          {params.get("q")
            ? `Результаты поиска «${params.get("q")}»`
            : "Все фильмы"}
        </span>
        <span>
          {movies.data ? `${movies.data.total} в подборке` : "Загрузка…"}
        </span>
      </div>
      {movies.loading ? (
        <Loading />
      ) : movies.error ? (
        <ErrorPanel error={movies.error} retry={movies.reload} />
      ) : !movies.data.items.length ? (
        <EmptyState filtered={params.size > 0} reset={reset} />
      ) : (
        <div className="movie-grid">
          {movies.data.items.map((movie) => (
            <MovieCard key={movie.id} movie={movie} onDelete={setDeleting} />
          ))}
        </div>
      )}
      {movies.data && <Pagination data={movies.data} onPage={goPage} />}
      {deleting && (
        <DeleteDialog
          movie={deleting}
          onCancel={() => setDeleting(null)}
          onDeleted={onDeleted}
        />
      )}
    </div>
  );
}

function Search() {
  const [params, setParams] = useSearchParams();
  const initial = () =>
    Object.fromEntries(FILTER_KEYS.map((key) => [key, params.get(key) || ""]));
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [deleting, setDeleting] = useState(null);
  const [revision, setRevision] = useState(0);
  const genres = useResource("/api/v1/genres");
  const movies = useResource(
    `/api/v1/movies?${movieQuery(params, { pageSize: 6 })}`,
    revision,
  );
  const { notify } = useOutletContext();
  useEffect(() => {
    setValues(
      Object.fromEntries(
        FILTER_KEYS.map((key) => [key, params.get(key) || ""]),
      ),
    );
    setErrors({});
  }, [params]);
  function submit(event) {
    event.preventDefault();
    const found = validateFilters(values);
    setErrors(found);
    if (Object.keys(found).length) {
      event.currentTarget.elements.namedItem(Object.keys(found)[0])?.focus();
      return;
    }
    const next = new URLSearchParams();
    FILTER_KEYS.forEach((key) => {
      if (values[key].trim()) next.set(key, values[key].trim());
    });
    for (const key of ["sort_by", "order"])
      if (params.get(key)) next.set(key, params.get(key));
    setParams(next);
  }
  function reset() {
    setValues(Object.fromEntries(FILTER_KEYS.map((key) => [key, ""])));
    setErrors({});
    setParams({});
  }
  function control(key, extra = {}) {
    return (id, errorId) => (
      <input
        id={id}
        name={key}
        value={values[key]}
        onChange={(event) =>
          setValues({ ...values, [key]: event.target.value })
        }
        aria-invalid={!!errors[key]}
        aria-describedby={errorId}
        {...extra}
      />
    );
  }
  function goPage(page) {
    const next = new URLSearchParams(params);
    next.set("page", page);
    setParams(next);
  }
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow section-kicker">
            <span />
            НАЙДИТЕ СВОЮ ИСТОРИЮ
          </p>
          <h1>
            Кино по настроению<span className="title-dot">.</span>
          </h1>
          <p className="page-description">
            Название, жанр или год - начните с того, что помните.
          </p>
        </div>
      </div>
      <div className="search-layout">
        <form className="filters-panel" onSubmit={submit} noValidate>
          <div className="panel-title">
            <Icon name="filter" size={18} />
            <h2>Фильтры</h2>
          </div>
          <Field label="Название фильма" error={errors.q}>
            {control("q", { placeholder: "Например, Орбита", maxLength: 200 })}
          </Field>
          <Field label="Жанр" error={errors.genre}>
            {(id) => (
              <select
                id={id}
                name="genre"
                value={values.genre}
                onChange={(event) =>
                  setValues({ ...values, genre: event.target.value })
                }
              >
                <option value="">Все жанры</option>
                {values.genre && !genres.data?.includes(values.genre) && (
                  <option value={values.genre}>{values.genre}</option>
                )}
                {genres.data?.map((genre) => (
                  <option key={genre}>{genre}</option>
                ))}
              </select>
            )}
          </Field>
          {genres.error && (
            <p className="field-error">
              Жанры не загружены.{" "}
              <button
                type="button"
                className="text-button"
                onClick={genres.reload}
              >
                Повторить
              </button>
            </p>
          )}
          <Field label="Год выпуска" error={errors.year}>
            {control("year", {
              type: "number",
              min: 1888,
              max: 2100,
              step: 1,
              placeholder: "Любой год",
            })}
          </Field>
          <p className="range-title">Рейтинг</p>
          <div className="rating-range">
            <Field label="От" error={errors.rating_min}>
              {control("rating_min", {
                type: "number",
                min: 0,
                max: 10,
                step: 0.1,
                placeholder: "0",
              })}
            </Field>
            <span>—</span>
            <Field label="До" error={errors.rating_max}>
              {control("rating_max", {
                type: "number",
                min: 0,
                max: 10,
                step: 0.1,
                placeholder: "10",
              })}
            </Field>
          </div>
          <button className="button full-width" type="submit">
            <Icon name="search" size={17} />
            Найти фильмы
          </button>
          <button className="reset-button" type="button" onClick={reset}>
            Сбросить фильтры
          </button>
        </form>
        <section className="search-results" aria-label="Результаты поиска">
          <div className="search-results-heading">
            <div>
              <h2>Результаты поиска</h2>
              <p>
                {movies.data
                  ? `Найдено: ${movies.data.total}`
                  : movies.error
                    ? "Запрос не выполнен"
                    : "Ищем фильмы…"}
              </p>
            </div>
            <SortControl params={params} setParams={setParams} />
          </div>
          {movies.loading ? (
            <Loading label="Ищем подходящие фильмы…" />
          ) : movies.error ? (
            <ErrorPanel error={movies.error} retry={movies.reload} />
          ) : !movies.data.items.length ? (
            <EmptyState filtered reset={reset} />
          ) : (
            <div className="movie-grid search-grid">
              {movies.data.items.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={movie}
                  onDelete={setDeleting}
                />
              ))}
            </div>
          )}
          {movies.data && <Pagination data={movies.data} onPage={goPage} />}
        </section>
      </div>
      {deleting && (
        <DeleteDialog
          movie={deleting}
          onCancel={() => setDeleting(null)}
          onDeleted={() => {
            setDeleting(null);
            notify("Фильм удалён из коллекции");
            if (movies.data?.items.length === 1 && movies.data.page > 1)
              goPage(movies.data.page - 1);
            setRevision((v) => v + 1);
            genres.reload();
          }}
        />
      )}
    </div>
  );
}

const newMovie = {
  title: "",
  director: "",
  genre: "",
  year: "",
  rating: "",
  duration_minutes: "",
  description: "",
};

function MovieForm({ movie }) {
  const [values, setValues] = useState(
    movie
      ? Object.fromEntries(
          Object.keys(newMovie).map((key) => [
            key,
            movie[key] == null ? "" : String(movie[key]),
          ]),
        )
      : newMovie,
  );
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const { notify } = useOutletContext();
  const genres = useResource("/api/v1/genres");
  async function save(event) {
    event.preventDefault();
    if (busy) return;
    const found = validateMovie(values);
    setErrors(found);
    setFailure(null);
    if (Object.keys(found).length) {
      event.currentTarget.elements.namedItem(Object.keys(found)[0])?.focus();
      return;
    }
    setBusy(true);
    try {
      const saved = await request(
        movie ? `/api/v1/movies/${movie.id}` : "/api/v1/movies",
        { method: movie ? "PUT" : "POST", body: moviePayload(values) },
      );
      notify(movie ? "Изменения сохранены" : "Фильм добавлен в коллекцию");
      navigate(`/movies/${saved.id}`);
    } catch (error) {
      setErrors(error.fields || {});
      setFailure(error.message);
      setBusy(false);
    }
  }
  function field(key, extra = {}) {
    return (id, errorId) => (
      <input
        id={id}
        name={key}
        value={values[key]}
        onChange={(event) => {
          setValues({ ...values, [key]: event.target.value });
          if (errors[key]) setErrors({ ...errors, [key]: undefined });
        }}
        aria-invalid={!!errors[key]}
        aria-describedby={errorId}
        {...extra}
      />
    );
  }
  return (
    <div className="editor-layout">
      <form className="movie-form" onSubmit={save} noValidate>
        <fieldset disabled={busy}>
          <legend className="sr-only">Карточка фильма</legend>
          <div className="form-section-heading">
            <span>01</span>
            <div>
              <h2>Главное о фильме</h2>
              <p>Всё, что поможет узнать его с первого взгляда.</p>
            </div>
          </div>
          <Field label="Название фильма" error={errors.title}>
            {field("title", {
              placeholder: "Как называется ваша следующая история?",
              maxLength: 200,
              required: true,
            })}
          </Field>
          <Field label="Режиссёр" error={errors.director}>
            {field("director", {
              placeholder: "Имя и фамилия",
              maxLength: 120,
              required: true,
            })}
          </Field>
          <div className="form-row">
            <Field label="Год выпуска" error={errors.year}>
              {field("year", {
                type: "number",
                min: 1888,
                max: 2100,
                step: 1,
                placeholder: "2024",
                required: true,
              })}
            </Field>
            <Field label="Жанр" error={errors.genre}>
              {field("genre", {
                placeholder: "Например, Драма",
                maxLength: 60,
                list: "movie-genres",
                required: true,
              })}
            </Field>
          </div>
          <datalist id="movie-genres">
            {genres.data?.map((genre) => (
              <option key={genre} value={genre} />
            ))}
          </datalist>
          <div className="form-row">
            <Field label="Рейтинг" error={errors.rating}>
              {field("rating", {
                type: "number",
                min: 0,
                max: 10,
                step: "any",
                placeholder: "От 0 до 10",
                required: true,
              })}
            </Field>
            <Field label="Длительность, мин" error={errors.duration_minutes}>
              {field("duration_minutes", {
                type: "number",
                min: 1,
                max: 1000,
                step: 1,
                placeholder: "110",
                required: true,
              })}
            </Field>
          </div>
          <div className="form-section-heading second-section">
            <span>02</span>
            <div>
              <h2>Немного больше</h2>
              <p>Сюжет, впечатление или причина посмотреть.</p>
            </div>
          </div>
          <Field label="Описание" optional error={errors.description}>
            {(id, errorId) => (
              <textarea
                id={id}
                name="description"
                value={values.description}
                onChange={(event) =>
                  setValues({ ...values, description: event.target.value })
                }
                maxLength={3000}
                rows={4}
                placeholder="О чём этот фильм?"
                aria-invalid={!!errors.description}
                aria-describedby={errorId}
              />
            )}
          </Field>
          <p className="character-counter">
            {values.description.length} / 3000
          </p>
        </fieldset>
        {failure && (
          <p className="form-error" role="alert">
            <Icon name="alert" size={18} />
            {failure}
          </p>
        )}
        {Object.values(errors).some(Boolean) && !failure && (
          <p className="error-text" role="alert">
            Проверьте выделенные поля.
          </p>
        )}
        <div className="form-actions">
          <button className="button" type="submit" disabled={busy}>
            <Icon name={movie ? "check" : "plus"} size={18} />
            {busy
              ? "Сохраняем…"
              : movie
                ? "Сохранить изменения"
                : "Добавить в коллекцию"}
          </button>
          <button
            className="button ghost"
            type="button"
            disabled={busy}
            onClick={() => navigate(movie ? `/movies/${movie.id}` : "/")}
          >
            Отмена
          </button>
        </div>
      </form>
      <aside className="form-preview">
        <p className="eyebrow">ТАК ВАШ ФИЛЬМ УВИДЯТ В КОЛЛЕКЦИИ</p>
        <Poster movie={{ ...values, id: movie?.id || 1 }} />
        <div className="preview-meta">
          <span className="eyebrow">
            {values.genre || "ЖАНР"} · {values.year || "ГОД"}
          </span>
          <h2>{values.title || "Название вашей истории"}</h2>
          <p>{values.director || "Имя режиссёра"}</p>
        </div>
        <div className="preview-note">
          <Icon name="film" size={23} />
          <p>
            У каждой истории есть место.
            <br />
            Добавьте её в свою коллекцию.
          </p>
        </div>
      </aside>
    </div>
  );
}

function Editor() {
  const { id } = useParams();
  const resource = useResource(id ? `/api/v1/movies/${id}` : null);
  return (
    <div className="page editor-page">
      <Link className="back-link" to={id ? `/movies/${id}` : "/"}>
        <Icon name="back" size={17} />
        {id ? "К фильму" : "К коллекции"}
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow section-kicker">
            <span />
            {id ? "НОВЫЙ ВЗГЛЯД НА ИСТОРИЮ" : "КОЛЛЕКЦИЯ СТАНОВИТСЯ БОЛЬШЕ"}
          </p>
          <h1>
            {id ? "Редактировать фильм" : "Добавить фильм"}
            <span className="title-dot">.</span>
          </h1>
          <p className="page-description">
            {id
              ? "Обновите детали, чтобы ничего не упустить."
              : "Заполните карточку. Остальное - дело кино."}
          </p>
        </div>
      </div>
      {id && resource.loading ? (
        <Loading label="Загружаем карточку фильма…" />
      ) : resource.error ? (
        <ErrorPanel error={resource.error} retry={resource.reload} />
      ) : (
        <MovieForm key={id || "new"} movie={id ? resource.data : null} />
      )}
    </div>
  );
}

function Details() {
  const { id } = useParams();
  const movie = useResource(`/api/v1/movies/${id}`);
  const [deleting, setDeleting] = useState(false);
  const { notify } = useOutletContext();
  const navigate = useNavigate();
  return (
    <div className="page detail-page">
      <Link className="back-link" to="/">
        <Icon name="back" size={17} />К коллекции
      </Link>
      {movie.loading ? (
        <Loading label="Открываем вашу историю…" />
      ) : movie.error ? (
        <ErrorPanel error={movie.error} retry={movie.reload} />
      ) : (
        <>
          <div className="detail-layout">
            <div className="detail-art">
              <Poster movie={movie.data} large />
              <div className="art-footer">
                <span>КАДР / ЛИЧНАЯ КОЛЛЕКЦИЯ</span>
                <span>№ {String(movie.data.id).padStart(3, "0")}</span>
              </div>
            </div>
            <div className="detail-content">
              <p className="eyebrow section-kicker">
                <span />
                {movie.data.genre} / {movie.data.year}
              </p>
              <h1>
                {movie.data.title}
                <span className="title-dot">.</span>
              </h1>
              <div className="detail-rating">
                <span>
                  <Icon name="star" size={19} />
                  {numberFormat.format(movie.data.rating)}
                </span>
                <span>из 10 · ваш рейтинг</span>
              </div>
              <dl className="movie-facts">
                <div>
                  <dt>Режиссёр</dt>
                  <dd>{movie.data.director}</dd>
                </div>
                <div>
                  <dt>Год выпуска</dt>
                  <dd>{movie.data.year}</dd>
                </div>
                <div>
                  <dt>Жанр</dt>
                  <dd>{movie.data.genre}</dd>
                </div>
                <div>
                  <dt>Длительность</dt>
                  <dd>{movie.data.duration_minutes} мин</dd>
                </div>
              </dl>
              <div className="movie-description">
                <h2>Об этой истории</h2>
                <p>
                  {movie.data.description ||
                    "Описание пока не добавлено. Расскажите, чем вам запомнился этот фильм."}
                </p>
              </div>
              <div className="detail-actions">
                <Link className="button" to={`/movies/${id}/edit`}>
                  <Icon name="edit" size={17} />
                  Редактировать
                </Link>
                <button
                  className="button secondary danger-text"
                  onClick={() => setDeleting(true)}
                >
                  <Icon name="trash" size={17} />
                  Удалить
                </button>
              </div>
            </div>
          </div>
          <div className="detail-bottom-note">
            <span className="small-mark">к</span>
            <p>
              Истории заканчиваются.
              <br />
              <strong>Хорошее кино остаётся.</strong>
            </p>
            <Link className="text-link" to="/">
              Больше историй в коллекции
              <Icon name="arrow" size={18} />
            </Link>
          </div>
        </>
      )}
      {deleting && (
        <DeleteDialog
          movie={movie.data}
          onCancel={() => setDeleting(false)}
          onDeleted={() => {
            notify("Фильм удалён из коллекции");
            navigate("/");
          }}
        />
      )}
    </div>
  );
}

function NotFound() {
  return (
    <div className="page">
      <ErrorPanel
        error={{
          status: 404,
          message: "Такой страницы нет. Вернитесь к своей коллекции.",
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main-content">
        К содержимому
      </a>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Collection />} />
          <Route path="search" element={<Search />} />
          <Route path="movies/new" element={<Editor />} />
          <Route path="movies/:id/edit" element={<Editor />} />
          <Route path="movies/:id" element={<Details />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}

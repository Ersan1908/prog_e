import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { request } from "./api.js";

const paths = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
  search: (
    <>
      <circle cx="10.8" cy="10.8" r="7" />
      <path d="m16 16 5 5" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  back: <path d="M20 12H4m6-6-6 6 6 6" />,
  edit: (
    <>
      <path d="m15 5 4 4M4 20l5-1L21 7a2.8 2.8 0 0 0-4-4L5 15l-1 5Z" />
    </>
  ),
  trash: (
    <>
      <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7" />
    </>
  ),
  filter: (
    <>
      <path d="M4 6h16M4 12h16M4 18h16" />
      <circle cx="8" cy="6" r="2" />
      <circle cx="16" cy="12" r="2" />
      <circle cx="10" cy="18" r="2" />
    </>
  ),
  close: <path d="m6 6 12 12M6 18 18 6" />,
  star: (
    <path d="m12 3 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z" />
  ),
  film: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M7 4v16M17 4v16M3 9h4m-4 6h4m10-6h4m-4 6h4" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  alert: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6m0 3v1" />
    </>
  ),
  chevron: <path d="m9 5 7 7-7 7" />,
};

export function Icon({ name, size = 20, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {paths[name] || paths.film}
    </svg>
  );
}

export function useResource(path, revision = 0) {
  const [state, setState] = useState({
    data: null,
    loading: Boolean(path),
    error: null,
  });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!path) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });
    request(path, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted)
          setState({ data, loading: false, error: null });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({ data: null, loading: false, error });
      });
    return () => controller.abort();
  }, [path, revision, retry]);
  return { ...state, reload: () => setRetry((value) => value + 1) };
}

export function Loading({ label = "Загружаем вашу коллекцию…" }) {
  return (
    <div className="state-panel" role="status">
      <span className="spinner" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorPanel({ error, retry }) {
  return (
    <div className="state-panel error-panel" role="alert">
      <Icon name="alert" size={30} />
      <h2>
        {error.status === 404
          ? "Фильм не найден"
          : "Не получилось загрузить данные"}
      </h2>
      <p>{error.message}</p>
      <div className="button-row">
        {retry && (
          <button className="button secondary" onClick={retry}>
            Попробовать снова
          </button>
        )}
        <Link className="text-link" to="/">
          Вернуться к коллекции <Icon name="arrow" size={17} />
        </Link>
      </div>
    </div>
  );
}

export function EmptyState({ filtered = false, reset }) {
  return (
    <div className="state-panel empty-state">
      <div className="empty-icon">
        <Icon name={filtered ? "search" : "film"} size={34} />
      </div>
      <h2>{filtered ? "Пока без совпадений" : "Первый кадр - за вами"}</h2>
      <p>
        {filtered
          ? "Попробуйте другое название или измените фильтры."
          : "Добавьте первый фильм, чтобы начать свою коллекцию."}
      </p>
      {filtered ? (
        <button className="button secondary" onClick={reset}>
          Сбросить поиск
        </button>
      ) : (
        <Link className="button" to="/movies/new">
          <Icon name="plus" size={18} />
          Добавить фильм
        </Link>
      )}
    </div>
  );
}

const palettes = {
  Фантастика: ["#192f39", "#d2b989", "#91aaa4", "#547980"],
  Драма: ["#be765b", "#f1d7b4", "#8d5548", "#e7b889"],
  Триллер: ["#292e35", "#c2bba3", "#5d6965", "#8d997f"],
  Комедия: ["#deb964", "#f9e6ae", "#a75943", "#f1d185"],
  Приключения: ["#536954", "#e9cc97", "#a1af8c", "#798c66"],
};

export function Poster({ movie, large = false }) {
  const [dark, light, mid, secondary] = palettes[movie.genre] || [
    "#6c7771",
    "#edddbb",
    "#3b5049",
    "#a4ae96",
  ];
  const variant = (movie.id || 1) % 3;
  return (
    <div
      className={`poster${large ? " poster-large" : ""}`}
      style={{ background: dark }}
    >
      <svg
        viewBox="0 0 400 300"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <rect width="400" height="300" fill={dark} />
        {movie.genre === "Фантастика" ? (
          <>
            <circle
              cx={variant === 0 ? 260 : 230}
              cy="111"
              r="67"
              fill={light}
            />
            <ellipse
              cx="232"
              cy="114"
              rx="116"
              ry="20"
              fill="none"
              stroke={mid}
              strokeWidth="2"
              transform="rotate(-27 232 114)"
            />
            <path d="M0 252 119 174 251 273 400 213v87H0Z" fill={secondary} />
            <path d="m0 284 154-75 115 91H0Z" fill={mid} />
            {[25, 62, 110, 179, 306, 355, 376].map((x, i) => (
              <circle
                key={x}
                cx={x}
                cy={35 + ((i * 31) % 135)}
                r="1.4"
                fill={light}
              />
            ))}
            <path
              d="M197 241v-20l6-8 6 8v20m-16-11h20"
              stroke={dark}
              strokeWidth="3"
              fill="none"
            />
          </>
        ) : movie.genre === "Драма" ? (
          <>
            <circle cx="298" cy="77" r="45" fill={light} />
            <path
              d="M0 191h66V91h61v75h61V58h51v149h67V141h94v159H0Z"
              fill={mid}
            />
            <path d="M0 241h67v-36h85v32h70v-63h78v55h100v71H0Z" fill={dark} />
            <path d="m133 300 51-139h26l57 139" fill={secondary} />
            <path
              d="m198 300-1-107"
              stroke={light}
              strokeWidth="2"
              strokeDasharray="14 18"
            />
            <path
              d="M91 125h12m-12 18h12m99-59h10m-10 18h10m123 64h12"
              stroke={light}
              strokeWidth="5"
            />
          </>
        ) : movie.genre === "Триллер" ? (
          <>
            <rect x="134" y="50" width="132" height="216" rx="65" fill={mid} />
            <path d="M185 295 183 86h34l-2 209" fill={light} />
            <path d="m217 86 94 214H217" fill={secondary} />
            <circle cx="200" cy="208" r="9" fill={dark} />
            <path d="m194 216-7 47h26l-8-47" fill={dark} />
            <path
              d="M50 0v300M100 0v300M300 0v300M350 0v300"
              stroke={light}
              strokeWidth="1"
              opacity=".08"
            />
          </>
        ) : movie.genre === "Комедия" ? (
          <>
            <circle cx="288" cy="73" r="42" fill={light} />
            <path d="M0 215q100-48 200 0t200 0v85H0Z" fill={secondary} />
            <path d="M0 250q100-48 200 0t200 0v50H0Z" fill={mid} />
            <path
              d="M93 198V109m-52 0q52-81 104 0Z"
              fill={light}
              stroke={light}
              strokeWidth="3"
            />
            <path
              d="M252 263v-35m-23 34 24-24 24 24M144 225v-29m-21 29 21-19 21 19"
              stroke={dark}
              strokeWidth="5"
            />
          </>
        ) : (
          <>
            <circle cx="287" cy="77" r="43" fill={light} />
            <path d="m0 248 133-176 161 228H0Z" fill={mid} />
            <path d="m173 300 119-174 108 161v13Z" fill={secondary} />
            <path d="m105 110 28-38 39 55-39-16-12 10Z" fill={light} />
            <path d="m0 270 91-71 112 101H0Z" fill={dark} />
            <path
              d="M272 300q-78-20-60-39t-16-24"
              fill="none"
              stroke={light}
              strokeWidth="5"
            />
          </>
        )}
        <rect
          x="14"
          y="14"
          width="372"
          height="272"
          rx="1"
          fill="none"
          stroke={light}
          strokeWidth=".8"
          opacity=".28"
        />
      </svg>
      <span className="poster-caption">
        КОЛЛЕКЦИЯ / {movie.year || "НОВЫЙ ФИЛЬМ"}
      </span>
    </div>
  );
}

export function MovieCard({ movie, onDelete }) {
  return (
    <article className="movie-card">
      <Link
        className="poster-link"
        to={`/movies/${movie.id}`}
        aria-label={`Подробнее о фильме «${movie.title}»`}
      >
        <Poster movie={movie} />
        <span className="rating">
          <Icon name="star" size={13} />
          {movie.rating.toFixed(1)}
        </span>
        <span className="poster-open">
          О фильме <Icon name="arrow" size={17} />
        </span>
      </Link>
      <div className="card-content">
        <p className="eyebrow">
          {movie.genre} <span>·</span> {movie.year}
        </p>
        <h2>
          <Link to={`/movies/${movie.id}`}>{movie.title}</Link>
        </h2>
        <p className="director">{movie.director}</p>
        <div className="card-footer">
          <span>{movie.duration_minutes} мин</span>
          <div className="card-actions">
            <Link
              className="icon-button"
              to={`/movies/${movie.id}/edit`}
              aria-label={`Редактировать «${movie.title}»`}
            >
              <Icon name="edit" size={16} />
            </Link>
            <button
              className="icon-button danger-icon"
              aria-label={`Удалить «${movie.title}»`}
              onClick={() => onDelete(movie)}
            >
              <Icon name="trash" size={16} />
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

export function Pagination({ data, onPage }) {
  if (data.total_pages <= 1 && data.page <= 1) return null;
  return (
    <nav className="pagination" aria-label="Пагинация">
      <span>
        Страница {data.page} из {data.total_pages || 1}
      </span>
      <div>
        <button
          className="page-button"
          aria-label="Предыдущая страница"
          disabled={data.page <= 1}
          onClick={() => onPage(data.page - 1)}
        >
          <Icon name="back" size={18} />
        </button>
        <button
          className="page-button"
          aria-label="Следующая страница"
          disabled={data.page >= data.total_pages}
          onClick={() => onPage(data.page + 1)}
        >
          <Icon name="arrow" size={18} />
        </button>
      </div>
    </nav>
  );
}

export function DeleteDialog({ movie, onCancel, onDeleted }) {
  const ref = useRef(null);
  const headingId = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await request(`/api/v1/movies/${movie.id}`, { method: "DELETE" });
      onDeleted();
    } catch (failure) {
      setError(failure);
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={ref}
      className="delete-dialog"
      aria-labelledby={headingId}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
    >
      <div className="delete-symbol">
        <Icon name="trash" size={25} />
      </div>
      <h2 id={headingId}>Удалить фильм?</h2>
      <p>
        «{movie.title}» исчезнет из вашей коллекции. Это действие нельзя
        отменить.
      </p>
      {error && (
        <p className="error-text" role="alert">
          {error.message}
        </p>
      )}
      <div className="button-row">
        <button
          className="button secondary"
          onClick={onCancel}
          disabled={busy}
          autoFocus
        >
          Оставить фильм
        </button>
        <button className="button danger" onClick={remove} disabled={busy}>
          {busy ? "Удаляем…" : "Удалить фильм"}
        </button>
      </div>
    </dialog>
  );
}

export function Field({ label, error, optional, children }) {
  const id = useId();
  return (
    <div className={`field${error ? " invalid" : ""}`}>
      <label htmlFor={id}>
        {label}
        {optional && <span>необязательно</span>}
      </label>
      {children(id, error ? `${id}-error` : undefined)}
      {error && (
        <span className="field-error" id={`${id}-error`}>
          {error}
        </span>
      )}
    </div>
  );
}

export const API_URL = (
  import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const messages = {
  string_too_short: "Поле не должно быть пустым.",
  string_too_long: "Слишком длинное значение.",
  greater_than_equal: "Значение меньше допустимого.",
  less_than_equal: "Значение больше допустимого.",
  int_type: "Введите целое число.",
  float_type: "Введите число.",
  missing: "Обязательное поле.",
};

export class ApiError extends Error {
  constructor(message, status = 0, fields = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

export function parseError(payload, status) {
  if (Array.isArray(payload?.detail)) {
    const fields = {};
    payload.detail.forEach((error) => {
      fields[error.loc?.at(-1) || "form"] = messages[error.type] || error.msg;
    });
    return new ApiError(
      "Проверьте значения в форме или параметрах поиска.",
      status,
      fields,
    );
  }
  return new ApiError(
    payload?.detail || `Сервер вернул ошибку ${status}.`,
    status,
  );
}

export function createApi(baseUrl = API_URL, fetcher = globalThis.fetch) {
  return async function request(path, { method = "GET", body, signal } = {}) {
    let response;
    try {
      response = await fetcher(`${baseUrl}${path}`, {
        method,
        headers:
          body === undefined
            ? undefined
            : { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal,
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new ApiError(
        "Не удалось связаться с сервером. Проверьте, что API запущен.",
      );
    }
    if (!response.ok) {
      let payload;
      try {
        payload = await response.json();
      } catch {
        payload = null;
      }
      throw parseError(payload, response.status);
    }
    // Ответ DELETE 204 не содержит JSON.
    return response.status === 204 ? null : response.json();
  };
}

export const request = createApi();

export function movieQuery(params, { pageSize = 8 } = {}) {
  const query = new URLSearchParams();
  for (const key of [
    "q",
    "year",
    "genre",
    "rating_min",
    "rating_max",
    "sort_by",
    "order",
  ]) {
    const value = params.get(key)?.trim();
    if (value) query.set(key, value);
  }
  const page = Math.min(
    1_000_000_000,
    Math.max(1, parseInt(params.get("page") || "1", 10) || 1),
  );
  query.set("page", String(page));
  query.set("page_size", String(pageSize));
  return query.toString();
}

export function validateMovie(values) {
  const errors = {};
  for (const [field, label, limit] of [
    ["title", "название фильма", 200],
    ["director", "режиссёра", 120],
    ["genre", "жанр", 60],
  ]) {
    if (!values[field].trim()) errors[field] = `Укажите ${label}.`;
    else if (values[field].trim().length > limit)
      errors[field] = `Максимум ${limit} символов.`;
  }
  for (const [field, label, min, max, integer] of [
    ["year", "Год", 1888, 2100, true],
    ["rating", "Рейтинг", 0, 10, false],
    ["duration_minutes", "Длительность", 1, 1000, true],
  ]) {
    const number = Number(values[field]);
    if (
      values[field] === "" ||
      !Number.isFinite(number) ||
      (integer && !Number.isInteger(number))
    ) {
      errors[field] = integer ? "Введите целое число." : "Введите число.";
    } else if (number < min || number > max)
      errors[field] = `${label}: от ${min} до ${max}.`;
  }
  if (values.description.trim().length > 3000)
    errors.description = "Максимум 3000 символов.";
  return errors;
}

export function moviePayload(values) {
  return {
    title: values.title.trim(),
    director: values.director.trim(),
    genre: values.genre.trim(),
    year: Number(values.year),
    rating: Number(values.rating),
    duration_minutes: Number(values.duration_minutes),
    description: values.description.trim() || null,
  };
}

export function validateFilters(values) {
  const errors = {};
  if (values.q.trim().length > 200) errors.q = "Максимум 200 символов.";
  if (values.genre.trim().length > 60) errors.genre = "Максимум 60 символов.";
  for (const [key, min, max] of [
    ["year", 1888, 2100],
    ["rating_min", 0, 10],
    ["rating_max", 0, 10],
  ]) {
    const value = values[key];
    if (
      value !== "" &&
      (!Number.isFinite(Number(value)) ||
        Number(value) < min ||
        Number(value) > max ||
        (key === "year" && !Number.isInteger(Number(value))))
    ) {
      errors[key] =
        `Допустимо от ${min} до ${max}${key === "year" ? ", целое число" : ""}.`;
    }
  }
  if (
    values.rating_min !== "" &&
    values.rating_max !== "" &&
    Number(values.rating_min) > Number(values.rating_max)
  ) {
    errors.rating_max = "Максимум не может быть меньше минимума.";
  }
  return errors;
}

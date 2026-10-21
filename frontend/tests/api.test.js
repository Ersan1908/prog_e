import assert from "node:assert/strict";
import { test } from "node:test";
import {
  ApiError,
  createApi,
  moviePayload,
  movieQuery,
  parseError,
  validateFilters,
  validateMovie,
} from "../src/api.js";

const valid = {
  title: "  Тестовый фильм ",
  director: " Автор ",
  genre: "Драма",
  year: "2024",
  rating: "8.2",
  duration_minutes: "110",
  description: "",
};

test("GET uses the configured API and AbortSignal", async () => {
  const controller = new AbortController();
  const api = createApi("http://api.test", async (url, options) => {
    assert.equal(url, "http://api.test/api/v1/movies");
    assert.equal(options.method, "GET");
    assert.equal(options.signal, controller.signal);
    assert.equal(options.body, undefined);
    assert.equal(options.headers, undefined);
    return Response.json({ items: [] });
  });
  assert.deepEqual(await api("/api/v1/movies", { signal: controller.signal }), {
    items: [],
  });
});

for (const method of ["POST", "PUT"])
  test(`${method} sends numeric JSON fields`, async () => {
    const body = moviePayload(valid);
    const api = createApi("http://api.test", async (_url, options) => {
      assert.equal(options.method, method);
      assert.equal(options.headers["Content-Type"], "application/json");
      assert.equal(JSON.parse(options.body).rating, 8.2);
      assert.equal(JSON.parse(options.body).description, null);
      return Response.json(
        { ...body, id: 5 },
        { status: method === "POST" ? 201 : 200 },
      );
    });
    assert.equal((await api("/movies", { method, body })).id, 5);
  });

test("DELETE 204 does not attempt to parse JSON", async () => {
  const api = createApi("http://api.test", async (_url, options) => {
    assert.equal(options.method, "DELETE");
    return new Response(null, { status: 204 });
  });
  assert.equal(await api("/movies/5", { method: "DELETE" }), null);
});

test("404 response is reported even though fetch resolves", async () => {
  const api = createApi("", async () =>
    Response.json({ detail: "Фильм не найден" }, { status: 404 }),
  );
  await assert.rejects(
    api("/movies/5"),
    (error) =>
      error instanceof ApiError &&
      error.status === 404 &&
      error.message === "Фильм не найден",
  );
});

test("422 field errors are available to form controls", () => {
  const error = parseError(
    {
      detail: [
        { loc: ["body", "rating"], type: "less_than_equal", msg: "bad rating" },
      ],
    },
    422,
  );
  assert.equal(error.status, 422);
  assert.ok(error.fields.rating);
});

test("non-JSON server error is handled", async () => {
  const api = createApi(
    "",
    async () => new Response("Server error", { status: 500 }),
  );
  await assert.rejects(api("/movies"), (error) => error.status === 500);
});

test("network failure gives an actionable error", async () => {
  const api = createApi("", async () => {
    throw new TypeError("Failed to fetch");
  });
  await assert.rejects(api("/movies"), /API запущен/);
});

test("cancellation remains AbortError", async () => {
  const api = createApi("", async () => {
    throw new DOMException("cancelled", "AbortError");
  });
  await assert.rejects(api("/movies"), (error) => error.name === "AbortError");
});

test("query keeps all supported filters, removes empty and unknown values", () => {
  const value = new URLSearchParams(
    "q= Орбита &year=2024&rating_min=8&genre= &unexpected=1",
  );
  const query = new URLSearchParams(movieQuery(value));
  assert.equal(query.get("q"), "Орбита");
  assert.equal(query.get("year"), "2024");
  assert.equal(query.get("rating_min"), "8");
  assert.equal(query.get("page_size"), "8");
  assert.equal(query.has("genre"), false);
  assert.equal(query.has("unexpected"), false);
});

test("pagination defaults and out-of-range page values are normalized", () => {
  assert.equal(
    new URLSearchParams(movieQuery(new URLSearchParams("page=-4"))).get("page"),
    "1",
  );
  assert.equal(
    new URLSearchParams(movieQuery(new URLSearchParams("page=oops"))).get(
      "page",
    ),
    "1",
  );
  assert.equal(
    new URLSearchParams(
      movieQuery(new URLSearchParams("page=99999999999"), { pageSize: 6 }),
    ).get("page"),
    "1000000000",
  );
});

test("payload trims strings, converts numeric fields and retains only editable properties", () => {
  assert.deepEqual(moviePayload({ ...valid, id: 4 }), {
    title: "Тестовый фильм",
    director: "Автор",
    genre: "Драма",
    year: 2024,
    rating: 8.2,
    duration_minutes: 110,
    description: null,
  });
  assert.equal(
    moviePayload({ ...valid, description: " Текст " }).description,
    "Текст",
  );
});

test("valid movie and inclusive limits pass validation", () => {
  assert.deepEqual(validateMovie(valid), {});
  assert.deepEqual(
    validateMovie({
      ...valid,
      year: "1888",
      rating: "0",
      duration_minutes: "1",
    }),
    {},
  );
  assert.deepEqual(
    validateMovie({
      ...valid,
      year: "2100",
      rating: "10",
      duration_minutes: "1000",
    }),
    {},
  );
});

test("required fields, oversized strings and numeric limits are checked", () => {
  const errors = validateMovie({
    title: " ",
    director: "",
    genre: "x".repeat(61),
    year: "1887",
    rating: "11",
    duration_minutes: "2.5",
    description: "x".repeat(3001),
  });
  assert.deepEqual(
    Object.keys(errors).sort(),
    [
      "title",
      "director",
      "genre",
      "year",
      "rating",
      "duration_minutes",
      "description",
    ].sort(),
  );
});

test("empty and non-finite numeric inputs are rejected", () => {
  assert.ok(validateMovie({ ...valid, year: "" }).year);
  assert.ok(validateMovie({ ...valid, rating: "Infinity" }).rating);
  assert.ok(
    validateMovie({ ...valid, duration_minutes: "NaN" }).duration_minutes,
  );
});

test("filter validation checks range order, year and rating limits", () => {
  const blank = { q: "", genre: "", year: "", rating_min: "", rating_max: "" };
  assert.deepEqual(validateFilters(blank), {});
  assert.ok(
    validateFilters({ ...blank, rating_min: "9", rating_max: "7" }).rating_max,
  );
  assert.ok(validateFilters({ ...blank, year: "2024.5" }).year);
  assert.ok(validateFilters({ ...blank, rating_min: "-1" }).rating_min);
  assert.ok(validateFilters({ ...blank, rating_max: "Infinity" }).rating_max);
});

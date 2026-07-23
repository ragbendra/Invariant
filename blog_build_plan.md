# Blog Project — Build Plan

Stack: FastAPI (Jinja2 SSR) · SQLAlchemy 2.0 · Alembic · PostgreSQL · Redis · Docker Compose · pytest

## How to use this document

Nine phases, in order. Each phase has: what you're building, the exact scope to hand an agentic tool for that phase (nothing more — don't let it touch later phases), and a validation checklist you run yourself before moving on. If validation fails, fix it before starting the next phase — don't let broken foundations compound.

Rule for agentic tools throughout: **never accept generated code for migrations, auth, or rate-limiting without reading it line by line.** These are the three places where "it ran without errors" and "it's correct" are different things. Everywhere else, running it and checking behavior against the validation checklist is sufficient.

---

## Target project structure

```
blog/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py          # engine, session factory
│   ├── models/
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── tag.py
│   │   └── comment.py
│   ├── schemas/              # Pydantic request/response models
│   ├── routers/
│   │   ├── posts.py
│   │   ├── auth.py
│   │   └── comments.py
│   ├── cache.py               # Redis wrapper functions
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── post_detail.html
│   │   └── partials/
│   │       ├── post_card.html
│   │       └── comments.html
│   └── static/
│       └── css/
├── alembic/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env
```

---

## Phase 0 — Repo & environment scaffold

**Build:** `pyproject.toml` with dependencies (fastapi, uvicorn, sqlalchemy>=2.0, alembic, psycopg2-binary, redis, jinja2, python-jose or itsdangerous for sessions, pytest, pytest-asyncio, fakeredis, testcontainers). Empty package structure above. `.env` for `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`.

**Agent scope:** scaffold generation only. Don't let it write business logic yet.

**Validation:**
- `uvicorn app.main:app --reload` boots with a placeholder `/health` route returning 200.
- No hardcoded secrets in committed files — `.env` is gitignored.

---

## Phase 1 — Database schema & models

**Build:** SQLAlchemy 2.0 models using `Mapped`/`mapped_column`:

```python
class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    title: Mapped[str]
    markdown_content: Mapped[str]
    excerpt: Mapped[str]
    published_at: Mapped[datetime | None]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tags: Mapped[list["Tag"]] = relationship(secondary="post_tags")
```

`User`, `Tag`, `post_tags` association table, and `Comment` (FK to `posts.id`, `body`, `author_name`, `created_at`, `approved: bool` for moderation).

Then `alembic init alembic`, configure `env.py` to import your `Base.metadata`, and generate the first migration.

**Agent scope:** models + one migration. Nothing else.

**Validation:**
- `alembic upgrade head` applies cleanly.
- `alembic downgrade -1` then `upgrade head` again — round-trips without error. If it doesn't, the migration has a bug an agent won't flag on its own.
- Inspect tables directly with `psql` — confirm FKs and indexes exist, don't just trust the migration ran.

---

## Phase 2 — Core read routes + unstyled Jinja2 skeleton

**Build:** `GET /` (paginated post list, published only, newest first), `GET /posts/{slug}` (404 if not found or unpublished). Bare-bones templates — no styling yet, just `{{ post.title }}` etc. rendering correctly with real DB data.

**Agent scope:** routes + template variable wiring. Explicitly tell it: no CSS, no styling, plain HTML only — you're validating data flow, not design, at this step.

**Validation:**
- Seed 3–4 posts directly via a script or `psql`, confirm they render in correct order.
- Hit `/posts/does-not-exist` — confirm a proper 404, not a 500.
- Unpublished post (`published_at IS NULL`) does not appear on `/` and 404s on direct URL.

---

## Phase 3 — Figma → code → Jinja2 (styling pass)

This is the phase you do incrementally, one template at a time, per your stated goal of validating generated code rather than accepting a full dump.

**Order:** base layout first, then post list, then post detail, then partials (post card, nav, footer). Doing base layout first means every subsequent page inherits validated header/nav/CSS instead of duplicating it.

**Per-template loop:**
1. Export or screenshot the relevant Figma frame.
2. Prompt the agent: convert this frame to static HTML + CSS. Explicitly state "no JavaScript framework, no build step, plain HTML/CSS" — otherwise it defaults to React/JSX, which you'd have to unwind.
3. Diff the output against what Phase 2 already has: identify which static text needs to become `{{ post.title }}`, `{{ post.excerpt }}`, `{{ post.published_at.strftime(...) }}`, and which repeated block (the post card) needs to become a `{% for %}` loop pulling from `partials/post_card.html`.
4. Make the substitution yourself, or have the agent do it but re-read the diff — this is where "generated code that looks right" and "generated code that's right" diverge, since an agent can silently drop a loop variable or hardcode what should be dynamic.
5. Render in browser, compare against the Figma frame at the same viewport width.

**Validation per template:**
- Renders with real seeded data, not placeholder text.
- No `<div>` soup left over from the AI conversion that doesn't correspond to anything in the Figma frame — dead markup is a common artifact of Figma-to-code tools.
- Responsive behavior checked at mobile width, not just desktop — most conversions get desktop right and mobile wrong.
- No `<script>` tags pulled in from a framework you didn't ask for (React runtime, Next.js hydration scripts) — check the rendered HTML source, not just the browser preview.

---

## Phase 4 — Redis caching layer

**Build:** `app/cache.py` with `get_cached_post(slug)` / `set_cached_post(slug, html, ttl=None)` / `invalidate_post(slug)`. Cache the **rendered post body HTML** (post-markdown-parsing), keyed `post:{slug}:html`. Do not cache the comment list in the same key — that's Phase 6's problem to keep separate.

Wire `invalidate_post(slug)` into the post-update route from Phase 5 (build this now, call it once auth exists).

**Agent scope:** the cache module only. Explain the invalidate-on-write requirement explicitly in your prompt — an agent given "add caching" with no further instruction will often default to TTL-only, which serves stale content after edits until expiry.

**Validation:**
- First request to a post: cache miss, log it, confirm DB hit.
- Second request: cache hit, no DB query (check via query logging or a counter).
- Edit the post (once Phase 5 exists): confirm next request is a cache miss again.

---

## Phase 5 — Admin auth & write routes

**Decision, not a question — this is server-rendered, not an API consumed by a separate frontend, so use session cookies (signed, httponly), not JWT.** JWT solves cross-origin/stateless-API auth, which you don't have here; a signed session cookie is simpler and doesn't require you to think about token storage or refresh logic in a browser context. Use `itsdangerous` for signing or a starlette session middleware.

**Build:** `/admin/login` (single admin user, or a `User` table with hashed passwords via `passlib`/`bcrypt`), `POST /admin/posts` (create), `PUT /admin/posts/{slug}` (edit, calls `invalidate_post`), `DELETE`. All admin routes behind a dependency that checks the session.

CSRF: since this is cookie-based session auth with HTML forms, you need CSRF protection on every state-changing POST/PUT/DELETE — cookies are sent automatically by the browser regardless of origin, so without a CSRF token a malicious page can trigger authenticated writes. Generate a token per session, embed as a hidden form field, validate server-side.

**Agent scope:** one route at a time. Read the auth dependency and CSRF check yourself — this is the security-critical code mentioned at the top.

**Validation:**
- Unauthenticated request to any `/admin/*` route → 401/redirect to login, not 200.
- Login with wrong password → rejected, no session set.
- Submit a write form with the CSRF token stripped → rejected.
- Editing a post via the admin route triggers `invalidate_post` — confirm via the Phase 4 cache-miss check.

---

## Phase 6 — Comments

**Build:** `POST /posts/{slug}/comments` (public, no auth), stores `approved=False` by default if you want moderation, or `True` if you're skipping moderation for v1. Comment list renders in `partials/comments.html`, included in the post template **outside** the cached HTML block from Phase 4 — the comment list queries Postgres directly on each request (cheap for a single post's comments; add a short TTL cache, 30–60s, only if you actually see load).

**Rate limiting (mechanism):** fixed-window counter in Redis. On each `POST`: `key = f"comment_rl:{ip}"`, `INCR key`, and if the result is 1 (first hit in this window) set `EXPIRE key 60`. Reject if the counter exceeds your threshold (e.g. 5) before the key expires. This is a fixed window, not sliding — it allows a burst at the window boundary (e.g. 5 at 0:59, 5 more at 1:00), which is an acceptable tradeoff for comment spam at this scale; don't over-engineer a sliding-window log unless you're actually seeing abuse.

**Agent scope:** route + rate-limit function. Trace the `INCR`/`EXPIRE` logic yourself — an off-by-one here (checking the limit before vs. after `INCR`) changes whether the limit is N or N+1.

**Validation:**
- Post a comment, confirm it appears without the post body cache being invalidated (check Phase 4's cache-hit counter stays unaffected).
- Submit 6 comments rapidly from the same source → 6th is rejected.
- Wait out the window (or manually expire the key in `redis-cli`) → next comment succeeds.

---

## Phase 7 — Test suite

**Build:**
- `tests/conftest.py`: Postgres via testcontainers (not sqlite — sqlite's relaxed typing and constraint enforcement will pass tests that fail against real Postgres), transactional rollback per test.
- Mock Redis with `fakeredis` for cache and rate-limit tests.
- Cover: CRUD routes, pagination boundaries, cache hit/miss/invalidate, auth rejection paths, CSRF rejection, rate-limit boundary (exactly at threshold, one over).

**Agent scope:** test files, one module at a time, after the corresponding phase is manually validated — don't generate tests for code you haven't reviewed yet, since the agent will write tests that pass against whatever bugs are already there.

**Validation:** `pytest -v`, all green, and spot-check that at least the auth and rate-limit tests actually fail if you deliberately break the logic (comment out the CSRF check, rerun — test should fail; if it doesn't, the test isn't testing what you think).

---

## Phase 8 — Dockerize

**Build:** `docker-compose.yml` — `web` (build from `Dockerfile`, depends_on `db` and `redis` with healthchecks, not just `depends_on` by name since that only waits for container start, not readiness), `db` (postgres image, volume for persistence), `redis`. Run `alembic upgrade head` as part of container startup (entrypoint script), not manually.

**Validation:**
- `docker compose up --build` from a clean state (no local `.venv`, no local Postgres) — full stack comes up, migrations apply, site is reachable.
- Kill the `db` container mid-run, restart it — `web` reconnects without needing a manual restart (confirms your SQLAlchemy engine pool handles reconnection).

---

## Phase 9 — Deployment (brief — revisit when you get there)

Out of scope for detailed planning now; when you're ready, the open items are: secrets management (don't ship `.env` — use your host's secret store), TLS termination (reverse proxy — nginx or Caddy — in front of uvicorn, not uvicorn directly exposed), and DB backups (`pg_dump` on a schedule, tested restore, not just backup). Ask for detail on this phase when you're actually there — deciding it now is premature.

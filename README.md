# Invariant Blog

Invariant is a FastAPI and Jinja2 server-rendered blog project. The build follows `blog_build_plan.md`, using SQLAlchemy models, Alembic migrations, and simple HTML/CSS templates that will be expanded phase by phase.

## Current Scope

- FastAPI app with a `/health` route.
- SQLAlchemy models for users, posts, tags, and comments.
- Alembic initial migration.
- Public blog routes:
  - `/` lists published posts.
  - `/posts/{slug}` shows one published post.
- Jinja2 frontend with reusable header, footer, and post card components.
- Classic editorial frontend style inspired by the templates in `templatedesign/`.

## Project Structure

```text
app/
  main.py
  config.py
  database.py
  models/
  routers/
  static/css/style.css
  templates/
    base.html
    index.html
    post_detail.html
    partials/
      header.html
      footer.html
      post_card.html
alembic/
scripts/
tests/
```

## Run Locally

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

## Notes

The frontend is intentionally being built in stages: global layout first, then the active page body, then future sections when the spec reaches them.

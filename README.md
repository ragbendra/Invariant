# Invariant Blog

Invariant is a FastAPI and Jinja2 server-rendered blog project for publishing articles with a clean editorial reading experience. It uses SQLAlchemy models, Alembic migrations, and reusable HTML/CSS templates.

## Current Scope

- FastAPI app with a `/health` route.
- SQLAlchemy models for users, posts, tags, and comments.
- Alembic initial migration.
- Public blog routes:
  - `/` lists published posts.
  - `/posts/{slug}` shows one published post.
- Jinja2 frontend with reusable header, footer, and post card components.
- Classic editorial frontend style inspired by the templates in `templatedesign/`.
- Markdown post content rendered as sanitized article HTML.
- Rendered post body caching through Redis when Redis is available.
- Personal and Travel layout studies populated with clearly labeled simulated data.

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
.\run_dev.ps1
```

Then open `http://127.0.0.1:8010`. Keep this development server running while editing; Uvicorn reloads Python, template, and static app changes on refresh.

## Docker Compose

Run the full PostgreSQL, Redis, and web stack with:

```powershell
docker compose up --build
```

The web container runs `alembic upgrade head` before starting Uvicorn. Open `http://127.0.0.1:8000` when the services report healthy.

## Quality Checks

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

GitHub Actions runs compilation, migrations, tests, and Compose validation on pushes and pull requests. Version tags such as `v1.0.0` publish a container image to GitHub Container Registry through the CD workflow.

## Frontend Approach

The frontend is organized like a maintainable server-rendered website:

- `base.html` provides the shared document shell.
- `header.html` and `footer.html` provide reusable site-wide navigation and closing content.
- `index.html` renders the published article listing.
- `post_card.html` renders each repeated article preview.
- `post_detail.html` renders the individual article page.

The visual direction takes inspiration from the classic grid and post-detail references in [`FigmaTemplate`](https://www.figma.com/community/file/1456300075957972581/free-blog-template-4-theme-blog-with-complete-ui), while the implemented functionality stays limited to the currently supported blog routes and database fields. Unsupported future features are represented only by non-functional layout placeholders.

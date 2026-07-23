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

## Frontend Approach

The frontend is organized like a maintainable server-rendered website:

- `base.html` provides the shared document shell.
- `header.html` and `footer.html` provide reusable site-wide navigation and closing content.
- `index.html` renders the published article listing.
- `post_card.html` renders each repeated article preview.
- `post_detail.html` renders the individual article page.

The visual direction takes inspiration from the classic grid and post-detail references in [`FigmaTemplate`](https://www.figma.com/community/file/1456300075957972581/free-blog-template-4-theme-blog-with-complete-ui), while the implemented functionality stays limited to the currently supported blog routes and database fields. Unsupported future features are represented only by non-functional layout placeholders.

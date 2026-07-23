from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.database import get_db
from app.markdown import render_markdown
from app.models.post import Post

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def post_list(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    per_page = 10
    offset = (page - 1) * per_page

    posts = (
        db.query(Post)
        .filter(Post.published_at.isnot(None))
        .order_by(Post.published_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total = db.query(Post).filter(Post.published_at.isnot(None)).count()
    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "posts": posts,
            "page": page,
            "total_pages": total_pages,
        },
    )


@router.get("/posts/{slug}")
def post_detail(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.published_at.isnot(None))
        .first()
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        request=request,
        name="post_detail.html",
        context={
            "post": post,
            "rendered_content": render_markdown(post.markdown_content),
        },
    )

from hmac import compare_digest

from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.auth import (
    get_current_user,
    get_optional_user,
    get_or_create_csrf_token,
    set_csrf_cookie,
)
from app.cache import get_cached_post, set_cached_post
from app.config import CSRF_COOKIE_NAME
from app.database import get_db
from app.demo_content import PERSONAL_PREVIEW, TRAVEL_PREVIEW
from app.markdown import render_markdown
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.rate_limit import allow_comment

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
            "personal_preview": PERSONAL_PREVIEW,
            "travel_preview": TRAVEL_PREVIEW,
        },
    )


@router.get("/posts/{slug}")
def post_detail(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.published_at.isnot(None))
        .first()
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    rendered_content = get_cached_post(post.slug)
    if rendered_content is None:
        rendered_content = render_markdown(post.markdown_content)
        set_cached_post(post.slug, rendered_content)

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post.id, Comment.approved.is_(True))
        .order_by(Comment.created_at.asc())
        .all()
    )
    csrf_token, should_set_cookie = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request=request,
        name="post_detail.html",
        context={
            "post": post,
            "rendered_content": rendered_content,
            "comments": comments,
            "current_user": current_user,
            "csrf_token": csrf_token,
        },
    )
    if should_set_cookie:
        set_csrf_cookie(response, csrf_token)
    return response


@router.post("/posts/{slug}/comments")
def create_comment(
    request: Request,
    slug: str,
    body: str = Form(...),
    csrf_token: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token or not compare_digest(csrf_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    ip_address = request.client.host if request.client else "unknown"
    if not allow_comment(ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many comments. Please try again later.",
            headers={"Retry-After": "60"},
        )

    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.published_at.isnot(None))
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if not body.strip():
        raise HTTPException(status_code=422, detail="Comment cannot be empty")

    db.add(
        Comment(
            post_id=post.id,
            user_id=current_user.id,
            author_name=current_user.username,
            body=body.strip(),
            approved=False,
        )
    )
    db.commit()
    return RedirectResponse(
        f"/posts/{post.slug}#comments",
        status_code=status.HTTP_303_SEE_OTHER,
    )

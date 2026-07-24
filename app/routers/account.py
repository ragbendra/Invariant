from datetime import datetime
from hmac import compare_digest

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.auth import get_current_user, get_or_create_csrf_token, set_csrf_cookie
from app.cache import invalidate_post
from app.config import CSRF_COOKIE_NAME
from app.database import get_db
from app.models.post import Post
from app.models.user import User

router = APIRouter(tags=["account"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/account/posts/new")
def new_post_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    csrf_token, should_set_cookie = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request=request,
        name="post_form.html",
        context={"csrf_token": csrf_token, "created": request.query_params.get("created")},
    )
    if should_set_cookie:
        set_csrf_cookie(response, csrf_token)
    return response


@router.post("/posts")
def create_post(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    excerpt: str = Form(...),
    markdown_content: str = Form(...),
    published_at: str = Form(""),
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

    if db.query(Post).filter(Post.slug == slug).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    parsed_published_at = None
    if published_at:
        try:
            parsed_published_at = datetime.fromisoformat(published_at)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="published_at must be a valid date and time",
            ) from exc

    post = Post(
        title=title,
        slug=slug,
        excerpt=excerpt,
        markdown_content=markdown_content,
        published_at=parsed_published_at,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    return RedirectResponse("/account/posts/new?created=1", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/account/posts/{slug}/edit")
def edit_post_page(
    request: Request,
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.author_id == current_user.id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    csrf_token, should_set_cookie = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request=request,
        name="post_form.html",
        context={
            "csrf_token": csrf_token,
            "post": post,
            "updated": request.query_params.get("updated"),
        },
    )
    if should_set_cookie:
        set_csrf_cookie(response, csrf_token)
    return response


@router.post("/account/posts/{slug}/edit")
@router.put("/posts/{slug}")
def update_post(
    request: Request,
    slug: str,
    title: str = Form(...),
    new_slug: str = Form(..., alias="slug"),
    excerpt: str = Form(...),
    markdown_content: str = Form(...),
    published_at: str = Form(""),
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

    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.author_id == current_user.id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    duplicate = (
        db.query(Post)
        .filter(Post.slug == new_slug, Post.id != post.id)
        .first()
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    parsed_published_at = None
    if published_at:
        try:
            parsed_published_at = datetime.fromisoformat(published_at)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="published_at must be a valid date and time",
            ) from exc

    old_slug = post.slug
    post.title = title
    post.slug = new_slug
    post.excerpt = excerpt
    post.markdown_content = markdown_content
    post.published_at = parsed_published_at
    db.commit()

    invalidate_post(old_slug)
    if new_slug != old_slug:
        invalidate_post(new_slug)

    if request.method == "PUT":
        return JSONResponse({"message": "Post updated", "slug": new_slug})
    return RedirectResponse(
        f"/account/posts/{new_slug}/edit?updated=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/account/posts/{slug}/delete")
@router.delete("/posts/{slug}")
def delete_post(
    request: Request,
    slug: str,
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

    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.author_id == current_user.id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    db.delete(post)
    db.commit()
    invalidate_post(slug)

    if request.method == "DELETE":
        return JSONResponse({"message": "Post deleted", "slug": slug})
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

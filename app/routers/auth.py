from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

import bcrypt

from app.auth import create_access_token
from app.config import AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, JWT_EXPIRE_MINUTES
from app.database import get_db
from app.models.user import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"registered": request.query_params.get("registered")},
    )


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )


@router.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters",
        )

    if db.query(User).filter((User.username == username) | (User.email == email)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        ) from exc

    return RedirectResponse("/login?registered=1", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    response = JSONResponse({"message": "Login successful"})
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=create_access_token(user.id),
        max_age=JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
    )
    return response

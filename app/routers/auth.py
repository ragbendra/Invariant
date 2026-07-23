from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

import bcrypt

from app.auth import create_access_token
from app.config import AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, JWT_EXPIRE_MINUTES
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin-auth"])
templates = Jinja2Templates(directory="app/templates")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
    )


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

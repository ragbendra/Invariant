from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.routers import posts

app = FastAPI(title="Blog App")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(posts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

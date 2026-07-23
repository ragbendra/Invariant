import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-for-dev")

from collections.abc import Generator
from datetime import datetime

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.cache as cache_module
import app.rate_limit as rate_limit_module
from app.database import Base, get_db
from app.main import app
from app.models.post import Post
from app.models.user import User


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(TEST_ENGINE)
    Base.metadata.create_all(TEST_ENGINE)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache_module, "redis_client", fake_redis)
    monkeypatch.setattr(rate_limit_module, "redis_client", fake_redis)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def published_post(db_session: Session) -> Post:
    user = User(
        username="author",
        email="author@example.com",
        hashed_password="$2b$12$placeholder-hash-for-tests",
    )
    db_session.add(user)
    db_session.flush()
    post = Post(
        slug="test-post",
        title="Test Post",
        excerpt="A test excerpt.",
        markdown_content="## Test body\n\n**Rendered** content.",
        published_at=datetime(2026, 1, 1),
        author_id=user.id,
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

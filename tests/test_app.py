import re

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User


def register_and_login(client, username="writer", email="writer@example.com"):
    registered = client.post(
        "/register",
        data={"username": username, "email": email, "password": "correct-password"},
        follow_redirects=False,
    )
    assert registered.status_code == 303
    logged_in = client.post(
        "/login",
        data={"username": username, "password": "correct-password"},
    )
    assert logged_in.status_code == 200
    assert "invariant_access_token" in client.cookies


def csrf_from(response):
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match, "CSRF token was not rendered"
    return match.group(1)


def test_public_home_and_post_detail(client, published_post):
    home = client.get("/")
    detail = client.get(f"/posts/{published_post.slug}")

    assert home.status_code == 200
    assert detail.status_code == 200
    assert "<h2>Test body</h2>" in detail.text
    assert "**Rendered**" not in detail.text


def test_missing_post_is_404(client):
    assert client.get("/posts/does-not-exist").status_code == 404


def test_registration_and_login(client, db_session):
    register_and_login(client)
    user = db_session.query(User).filter_by(username="writer").one()
    assert user.hashed_password != "correct-password"


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/login",
        data={"username": "missing", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "invariant_access_token" not in client.cookies


def test_protected_create_requires_jwt(client):
    response = client.get("/account/posts/new")
    assert response.status_code == 401


def test_create_post_requires_csrf(client, db_session):
    register_and_login(client)
    response = client.get("/account/posts/new")
    assert response.status_code == 200

    create_response = client.post(
        "/posts",
        data={
            "title": "No CSRF",
            "slug": "no-csrf",
            "excerpt": "Excerpt",
            "markdown_content": "Body",
            "csrf_token": "missing-token",
        },
    )
    assert create_response.status_code == 403
    assert db_session.query(Post).filter_by(slug="no-csrf").count() == 0


def test_create_edit_and_delete_belong_to_authenticated_user(client, db_session):
    register_and_login(client)
    create_page = client.get("/account/posts/new")
    csrf_token = csrf_from(create_page)

    created = client.post(
        "/posts",
        data={
            "title": "Owned Post",
            "slug": "owned-post",
            "excerpt": "Excerpt",
            "markdown_content": "Body",
            "published_at": "2026-01-02T12:00",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert created.status_code == 303
    post = db_session.query(Post).filter_by(slug="owned-post").one()

    edit_page = client.get(f"/account/posts/{post.slug}/edit")
    edit_csrf = csrf_from(edit_page)
    edited = client.post(
        f"/account/posts/{post.slug}/edit",
        data={
            "title": "Edited Post",
            "slug": "edited-post",
            "excerpt": "Updated excerpt",
            "markdown_content": "Updated body",
            "published_at": "2026-01-03T12:00",
            "csrf_token": edit_csrf,
        },
        follow_redirects=False,
    )
    assert edited.status_code == 303
    assert db_session.query(Post).filter_by(slug="edited-post").one().title == "Edited Post"

    delete_page = client.get("/account/posts/edited-post/edit")
    delete_csrf = csrf_from(delete_page)
    deleted = client.post(
        "/account/posts/edited-post/delete",
        data={"csrf_token": delete_csrf},
        follow_redirects=False,
    )
    assert deleted.status_code == 303
    assert db_session.query(Post).filter_by(slug="edited-post").count() == 0


def test_authenticated_comment_requires_csrf_and_is_rate_limited(client, db_session, published_post):
    register_and_login(client, username="commenter", email="commenter@example.com")
    detail_page = client.get(f"/posts/{published_post.slug}")
    csrf_token = csrf_from(detail_page)

    missing_csrf = client.post(
        f"/posts/{published_post.slug}/comments",
        data={"body": "No token", "csrf_token": "wrong"},
    )
    assert missing_csrf.status_code == 403

    for index in range(5):
        response = client.post(
            f"/posts/{published_post.slug}/comments",
            data={"body": f"Comment {index}", "csrf_token": csrf_token},
            follow_redirects=False,
        )
        assert response.status_code == 303

    limited = client.post(
        f"/posts/{published_post.slug}/comments",
        data={"body": "One too many", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert limited.status_code == 429
    assert db_session.query(Comment).count() == 5

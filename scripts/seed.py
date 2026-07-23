"""Seed script: insert test posts for Phase 2 validation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.database import SessionLocal
from app.models.user import User
from app.models.post import Post

db = SessionLocal()

# Create a test author
author = db.query(User).filter(User.username == "admin").first()
if not author:
    author = User(username="admin", email="admin@blog.com", hashed_password="placeholder")
    db.add(author)
    db.commit()
    db.refresh(author)
    print(f"Created user: {author.username}")

# Seed posts (3 published, 1 unpublished)
posts_data = [
    {
        "slug": "first-post",
        "title": "First Post",
        "markdown_content": "This is the content of the first post.",
        "excerpt": "A short excerpt for the first post.",
        "published_at": datetime(2026, 7, 20),
    },
    {
        "slug": "second-post",
        "title": "Second Post",
        "markdown_content": "This is the content of the second post.",
        "excerpt": "A short excerpt for the second post.",
        "published_at": datetime(2026, 7, 21),
    },
    {
        "slug": "third-post",
        "title": "Third Post",
        "markdown_content": "This is the content of the third post.",
        "excerpt": "A short excerpt for the third post.",
        "published_at": datetime(2026, 7, 22),
    },
    {
        "slug": "draft-post",
        "title": "Draft Post (Unpublished)",
        "markdown_content": "This post should NOT appear on the listing or be accessible.",
        "excerpt": "This is a draft.",
        "published_at": None,
    },
]

for data in posts_data:
    existing = db.query(Post).filter(Post.slug == data["slug"]).first()
    if not existing:
        post = Post(author_id=author.id, **data)
        db.add(post)
        print(f"  Seeded: {data['title']}")
    else:
        print(f"  Skipped (exists): {data['title']}")

db.commit()
db.close()
print("Done.")

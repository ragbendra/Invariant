from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.tag import post_tags

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tag import Tag
    from app.models.comment import Comment


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    markdown_content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=post_tags, back_populates="posts"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

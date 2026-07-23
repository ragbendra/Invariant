from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=func.now())
    approved: Mapped[bool] = mapped_column(default=False)

    post: Mapped["Post"] = relationship(back_populates="comments")

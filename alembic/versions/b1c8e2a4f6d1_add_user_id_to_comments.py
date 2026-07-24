"""associate comments with users

Revision ID: b1c8e2a4f6d1
Revises: 7cf2d4ed263d
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c8e2a4f6d1"
down_revision: Union[str, Sequence[str], None] = "7cf2d4ed263d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_comments_user_id_users",
        "comments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_comments_user_id_users", "comments", type_="foreignkey")
    op.drop_column("comments", "user_id")

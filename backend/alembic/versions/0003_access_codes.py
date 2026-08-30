"""access codes: users identified by a 5-digit code with a total generation limit

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-30

Учётка теперь — это 5-значный код. Суточный лимит заменён на общий: код даёт
фиксированное число генераций и после исчерпания перестаёт работать.
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("code", sa.String(length=5), nullable=True))
    op.create_index("ix_users_code", "users", ["code"], unique=True)
    op.add_column(
        "users",
        sa.Column("generations_limit", sa.Integer(), nullable=False, server_default="10"),
    )
    op.add_column("users", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("users", "daily_limit")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="200"),
    )
    op.drop_column("users", "last_used_at")
    op.drop_column("users", "generations_limit")
    op.drop_index("ix_users_code", table_name="users")
    op.drop_column("users", "code")

"""store which moderation categories rejected a prompt

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-30

Пункт 3.4 Соглашения: причина отказа гостю не раскрывается. Но пункт 8.1 даёт право
заявить возражение, и оператору нужно знать, на каком основании сработал автомат.
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generations",
        sa.Column("moderation_categories", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generations", "moderation_categories")

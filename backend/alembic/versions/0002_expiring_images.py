"""index for the image cleanup sweep

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-28

Уборщик каждые несколько минут ищет генерации с файлом на диске, которые старше TTL.
Частичный индекс держит эту выборку дешёвой, когда журнал вырастет.
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_generations_created_at_with_file",
        "generations",
        ["created_at"],
        postgresql_where="file_path IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("ix_generations_created_at_with_file", table_name="generations")

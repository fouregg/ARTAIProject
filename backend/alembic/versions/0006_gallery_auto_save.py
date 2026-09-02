"""mark gallery items saved automatically right after generation

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-01

Каждая удачная генерация теперь сразу попадает в галерею, чтобы её не терял тот,
кто обновил страницу. Но такие записи не должны удерживать файл от уборки, иначе
срок хранения перестанет работать: отличаем их флагом is_auto.
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gallery_items",
        sa.Column("is_auto", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("gallery_items", "is_auto")

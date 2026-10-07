"""Pixel fingerprints and one visible tile per generation.

Revision ID: 0007
Revises: 0006
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("generations", sa.Column("image_sha256", sa.String(64), nullable=True))
    op.create_index("ix_generations_image_sha256", "generations", ["image_sha256"])
    # Keep the earliest tile; preserve the other records for moderation history.
    op.execute("""
        UPDATE dome_items SET is_visible = false WHERE id IN (
            SELECT id FROM (
                SELECT id, row_number() OVER (
                    PARTITION BY generation_id ORDER BY position, id
                ) AS ordinal FROM dome_items WHERE is_visible
            ) ranked WHERE ordinal > 1
        )
    """)
    op.create_index("uq_dome_visible_generation", "dome_items", ["generation_id"],
                    unique=True, postgresql_where=sa.text("is_visible"))


def downgrade() -> None:
    op.drop_index("uq_dome_visible_generation", table_name="dome_items")
    op.drop_index("ix_generations_image_sha256", table_name="generations")
    op.drop_column("generations", "image_sha256")

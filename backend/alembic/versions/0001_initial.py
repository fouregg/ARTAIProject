"""initial schema: users, generations, gallery_items, dome_items

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "generations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt_original", sa.Text(), nullable=False),
        sa.Column("prompt_translated", sa.Text(), nullable=True),
        sa.Column("source_lang", sa.String(length=8), nullable=True),
        sa.Column("detected_lang", sa.String(length=8), nullable=True),
        sa.Column(
            "translation_degraded", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("size", sa.String(length=32), nullable=False),
        sa.Column("quality", sa.String(length=16), nullable=False),
        sa.Column("output_format", sa.String(length=8), nullable=False, server_default="png"),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_generations_user_id", "generations", ["user_id"])
    op.create_index("ix_generations_status", "generations", ["status"])

    op.create_table(
        "gallery_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "generation_id",
            sa.Uuid(),
            sa.ForeignKey("generations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_gallery_items_user_id", "gallery_items", ["user_id"])

    op.create_table(
        "dome_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "generation_id",
            sa.Uuid(),
            sa.ForeignKey("generations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_dome_items_generation_id", "dome_items", ["generation_id"])
    op.create_index("ix_dome_items_position", "dome_items", ["position"])


def downgrade() -> None:
    op.drop_table("dome_items")
    op.drop_table("gallery_items")
    op.drop_table("generations")
    op.drop_table("users")

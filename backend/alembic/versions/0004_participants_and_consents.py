"""participant profiles and consent records

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-30

Экран 1 терминала: анкета участника и две обязательные отметки. Пункт 12.1
Пользовательского соглашения требует хранить редакцию и хеш-сумму предъявленных
текстов, идентификаторы терминала и сессии, язык интерфейса и время акцепта.
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("middle_name", sa.String(length=120), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column(
            "is_legal_representative",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            sa.Integer(),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_key", sa.String(length=32), nullable=False),
        sa.Column("document_version", sa.String(length=16), nullable=False),
        sa.Column("document_sha256", sa.String(length=64), nullable=False),
        sa.Column("terminal_id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("ui_language", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])
    op.create_index("ix_consents_participant_id", "consents", ["participant_id"])


def downgrade() -> None:
    op.drop_table("consents")
    op.drop_table("participants")

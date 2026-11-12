"""Initial encrypted schema for users and medical_records.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-11 22:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_salt", sa.String(length=64), nullable=False),
        sa.Column("email_blind_index", sa.String(length=64), nullable=False),
        sa.Column("cpf_blind_index", sa.String(length=64), nullable=False),
        sa.Column("full_name_encrypted", sa.Text(), nullable=False),
        sa.Column("email_encrypted", sa.Text(), nullable=False),
        sa.Column("cpf_encrypted", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email_blind_index", "users", ["email_blind_index"], unique=True)
    op.create_index("ix_users_cpf_blind_index", "users", ["cpf_blind_index"], unique=True)

    op.create_table(
        "medical_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("blood_type_blind_index", sa.String(length=64), nullable=False),
        sa.Column("weight_kg_encrypted", sa.Text(), nullable=False),
        sa.Column("height_m_encrypted", sa.Text(), nullable=False),
        sa.Column("blood_type_encrypted", sa.Text(), nullable=False),
        sa.Column("allergies_encrypted", sa.Text(), nullable=False),
        sa.Column("diagnoses_encrypted", sa.Text(), nullable=False),
        sa.Column("medical_notes_encrypted", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medical_records_user_id", "medical_records", ["user_id"], unique=True)
    op.create_index(
        "ix_medical_records_blood_type_blind_index",
        "medical_records",
        ["blood_type_blind_index"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_medical_records_blood_type_blind_index", table_name="medical_records")
    op.drop_index("ix_medical_records_user_id", table_name="medical_records")
    op.drop_table("medical_records")
    op.drop_index("ix_users_cpf_blind_index", table_name="users")
    op.drop_index("ix_users_email_blind_index", table_name="users")
    op.drop_table("users")

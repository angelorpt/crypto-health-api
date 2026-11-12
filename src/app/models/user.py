"""Modelo ORM para a tabela `users` com colunas criptografadas e Blind Indexes."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medical_record import MedicalRecord


def _utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    """Entidade persistida de Usuário com PII criptografada (AES-256-GCM) e índices cegos (HMAC)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    # Salt exclusivo de 32 bytes (codificado em Base64 URL-safe) usado no HKDF com o Pepper do servidor
    user_salt: Mapped[str] = mapped_column(String(64), nullable=False)

    # Blind Indexes determinísticos (HMAC-SHA256 + Pepper) para buscas exatas e unicidade
    email_blind_index: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    cpf_blind_index: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    # Dados Pessoais (PII) criptografados com AES-256-GCM + chave HKDF do usuário + AAD
    full_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    cpf_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # Hash irreversível da senha (Argon2id + Salt aleatório + HMAC Pepper do servidor)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    medical_record: Mapped["MedicalRecord | None"] = relationship(
        "MedicalRecord",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

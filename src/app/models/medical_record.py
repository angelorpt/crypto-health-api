"""Modelo ORM para a tabela `medical_records` com prontuário médico 100% criptografado."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MedicalRecord(Base):
    """Prontuário médico onde todos os campos clínicos são criptografados por usuário."""

    __tablename__ = "medical_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Blind Index opcional para permitir busca de doadores/pacientes por tipo sanguíneo sem descriptografar a tabela
    blood_type_blind_index: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    # Campos médicos criptografados com AES-256-GCM + HKDF(Pepper + user_salt) + Nonce 96b + AAD
    # Mesmo que 1.000 pacientes pesem exatamente 80.0 kg ou tenham tipo O+, cada registro terá um ciphertext único!
    weight_kg_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    height_m_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    blood_type_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    allergies_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    diagnoses_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    medical_notes_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

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

    user: Mapped["User"] = relationship("User", back_populates="medical_record")

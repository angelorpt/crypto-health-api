"""Modelos ORM do SQLAlchemy 2.0 representando o esquema físico criptografado no banco."""

from app.models.medical_record import MedicalRecord
from app.models.user import User

__all__ = ["User", "MedicalRecord"]

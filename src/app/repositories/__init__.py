"""Camada de acesso a dados (Repositories) encapsulando consultas SQLAlchemy 2.0."""

from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository

__all__ = ["UserRepository", "MedicalRecordRepository"]

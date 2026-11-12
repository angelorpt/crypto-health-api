"""Repositório de persistência e consulta de `MedicalRecord`."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medical_record import MedicalRecord


class MedicalRecordRepository:
    """Encapsula todas as operações de banco de dados para a entidade `MedicalRecord`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, record: MedicalRecord) -> MedicalRecord:
        """Cria ou atualiza um prontuário médico no banco de dados."""
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_by_id(self, record_id: str) -> MedicalRecord | None:
        """Busca um prontuário pelo seu UUID carregando o usuário proprietário."""
        stmt = (
            select(MedicalRecord)
            .options(selectinload(MedicalRecord.user))
            .where(MedicalRecord.id == record_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> MedicalRecord | None:
        """Busca o prontuário médico associado a um `user_id`."""
        stmt = (
            select(MedicalRecord)
            .options(selectinload(MedicalRecord.user))
            .where(MedicalRecord.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_blood_type_blind_index(
        self, blood_type_blind_index: str
    ) -> list[MedicalRecord]:
        """Busca prontuários pelo Blind Index do tipo sanguíneo sem descriptografar o banco."""
        stmt = (
            select(MedicalRecord)
            .options(selectinload(MedicalRecord.user))
            .where(MedicalRecord.blood_type_blind_index == blood_type_blind_index)
            .order_by(MedicalRecord.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

"""Repositório de persistência e consulta de `User` usando Blind Indexes."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    """Encapsula todas as operações de banco de dados para a entidade `User`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        """Persiste um novo usuário no banco de dados."""
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Busca um usuário pelo UUID carregando seu prontuário médico."""
        stmt = select(User).options(selectinload(User.medical_record)).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_blind_index(self, email_blind_index: str) -> User | None:
        """Busca um usuário em O(1) pelo Blind Index do e-mail sem descriptografar a tabela."""
        stmt = (
            select(User)
            .options(selectinload(User.medical_record))
            .where(User.email_blind_index == email_blind_index)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cpf_blind_index(self, cpf_blind_index: str) -> User | None:
        """Busca um usuário em O(1) pelo Blind Index do CPF sem descriptografar a tabela."""
        stmt = (
            select(User)
            .options(selectinload(User.medical_record))
            .where(User.cpf_blind_index == cpf_blind_index)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        """Lista usuários cadastrados com paginação simples."""
        stmt = (
            select(User)
            .options(selectinload(User.medical_record))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, user: User) -> None:
        """Remove o usuário e seu prontuário médico em cascata."""
        await self._session.delete(user)
        await self._session.commit()

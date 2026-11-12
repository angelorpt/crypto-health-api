"""Injeção de dependências (Dependency Inversion Principle - SOLID) para os routers FastAPI."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.crypto import CryptoSuite, build_crypto_suite
from app.core.database import get_db_session
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository
from app.services.demo_service import DemoService
from app.services.medical_record_service import MedicalRecordService
from app.services.user_service import UserService


def get_crypto(settings: Settings = Depends(get_settings)) -> CryptoSuite:
    """Fornece a suíte criptográfica configurada com os Peppers do ambiente."""
    return build_crypto_suite(settings)


def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Fornece o repositório de usuários."""
    return UserRepository(session)


def get_medical_record_repo(
    session: AsyncSession = Depends(get_db_session),
) -> MedicalRecordRepository:
    """Fornece o repositório de prontuários médicos."""
    return MedicalRecordRepository(session)


def get_medical_record_service(
    record_repo: MedicalRecordRepository = Depends(get_medical_record_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    crypto: CryptoSuite = Depends(get_crypto),
) -> MedicalRecordService:
    """Fornece o serviço de prontuários médicos."""
    return MedicalRecordService(
        record_repo=record_repo,
        user_repo=user_repo,
        crypto=crypto,
    )


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    medical_service: MedicalRecordService = Depends(get_medical_record_service),
    crypto: CryptoSuite = Depends(get_crypto),
) -> UserService:
    """Fornece o serviço de usuários."""
    return UserService(
        user_repo=user_repo,
        medical_service=medical_service,
        crypto=crypto,
    )


def get_demo_service(
    user_repo: UserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
    crypto: CryptoSuite = Depends(get_crypto),
) -> DemoService:
    """Fornece o serviço de demonstração e auditoria criptográfica."""
    return DemoService(
        user_repo=user_repo,
        user_service=user_service,
        crypto=crypto,
    )

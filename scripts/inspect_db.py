"""Script CLI para demonstrar e inspecionar os dados criptografados no banco vs descriptografados."""

import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.crypto import build_crypto_suite
from app.core.database import Base
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository
from app.services.demo_service import DemoService
from app.services.medical_record_service import MedicalRecordService
from app.services.user_service import UserService


async def main() -> None:
    """Executa o seed de dois pacientes com 80.0 kg e exibe a prova criptográfica completa."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    crypto = build_crypto_suite()

    async with session_factory() as session:
        user_repo = UserRepository(session)
        med_repo = MedicalRecordRepository(session)
        med_service = MedicalRecordService(med_repo, user_repo, crypto)
        user_service = UserService(user_repo, med_service, crypto)
        demo_service = DemoService(user_repo, user_service, crypto)

        comparison = await demo_service.seed_and_compare_identical_data()
        tamper = await demo_service.run_tamper_checks(
            source_user_id=comparison.user_a_id,
            target_user_id=comparison.user_b_id,
        )

        output = {
            "seed_comparison": comparison.model_dump(),
            "tamper_checks": tamper.model_dump(),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

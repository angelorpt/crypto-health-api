"""Rotas dedicadas à Demonstração e Auditoria Criptográfica (Visão Banco vs Visão API)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_demo_service
from app.schemas.demo import (
    CryptoPlaygroundRequest,
    CryptoPlaygroundResponse,
    SeedComparisonResponse,
    TamperCheckRequest,
    TamperCheckResponse,
    UserCryptoInspectionResponse,
)
from app.services.demo_service import DemoService

router = APIRouter(
    prefix="/demo",
    tags=["Demo & Auditoria Criptográfica"],
)


@router.post(
    "/seed-comparison",
    response_model=SeedComparisonResponse,
    summary="Cria 2 usuários com dados médicos 100% iguais (ex: 80.0 kg, O+) e compara os textos cifrados",
)
async def seed_and_compare_identical_data(
    service: DemoService = Depends(get_demo_service),
) -> SeedComparisonResponse:
    """Demonstra que dois pacientes com peso `80.0 kg`, altura `1.75 m`, sangue `O+` e mesma senha
    possuem valores 100% diferentes no banco de dados.
    """
    return await service.seed_and_compare_identical_data()


@router.get(
    "/inspect-user/{user_id}",
    response_model=UserCryptoInspectionResponse,
    summary="Inspeciona lado a lado o valor bruto no banco (ciphertext, nonce, tag, salt, blind index) vs texto plano",
)
async def inspect_user_crypto(
    user_id: str,
    service: DemoService = Depends(get_demo_service),
) -> UserCryptoInspectionResponse:
    """Exibe a radiografia criptográfica completa de um usuário e seu prontuário médico."""
    return await service.inspect_user_crypto(user_id)


@router.post(
    "/tamper-check",
    response_model=TamperCheckResponse,
    summary="Simula ataques de adulteração e cópia de ciphertexts entre usuários/colunas no banco",
)
async def run_tamper_checks(
    payload: TamperCheckRequest | None = None,
    service: DemoService = Depends(get_demo_service),
) -> TamperCheckResponse:
    """Prova que copiar o ciphertext de `80.0 kg` do Usuário A para o Usuário B (ou para outra coluna)
    é bloqueado pela autenticação AEAD (AES-256-GCM + chave HKDF exclusiva + AAD).
    """
    req = payload or TamperCheckRequest()
    return await service.run_tamper_checks(
        source_user_id=req.source_user_id,
        target_user_id=req.target_user_id,
    )


@router.post(
    "/crypto-playground",
    response_model=CryptoPlaygroundResponse,
    summary="Playground interativo: teste a criptografia de qualquer valor (ex: '80.0') em tempo real",
)
async def crypto_playground(
    payload: CryptoPlaygroundRequest,
    service: DemoService = Depends(get_demo_service),
) -> CryptoPlaygroundResponse:
    """Executa em memória a derivação HKDF, AES-256-GCM, Blind Index HMAC e Argon2id para qualquer entrada."""
    return service.run_crypto_playground(payload)

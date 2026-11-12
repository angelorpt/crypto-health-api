"""Endpoint de verificação de saúde (Healthcheck) da aplicação."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["Healthcheck"])


@router.get(
    "/health",
    summary="Verifica a saúde e os algoritmos criptográficos ativos da API",
)
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Retorna o status operacional do serviço e resumo da suíte criptográfica."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "cryptography": {
            "field_encryption": "AES-256-GCM (AEAD, 96-bit random nonce, AAD bound)",
            "key_derivation": "HKDF-SHA256 (Server Encryption Pepper + 32-byte Per-User Salt)",
            "searchable_encryption": "HMAC-SHA256 Blind Index (Server Blind Index Pepper)",
            "password_hashing": "Argon2id + 16-byte Random Salt + HMAC-SHA256 Server Password Pepper",
        },
    }

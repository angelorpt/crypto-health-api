"""Rotas de Autenticação (Login JWT, Verificação Argon2id + Pepper e Perfil `/me`)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_crypto, get_user_repo, get_user_service
from app.core.config import Settings, get_settings
from app.core.crypto import CryptoSuite
from app.core.security import create_access_token, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    PasswordVerifyRequest,
    PasswordVerifyResponse,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Autenticação & Argon2id"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica usuário via Blind Index de e-mail + Argon2id/Pepper e emite JWT",
)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    crypto: CryptoSuite = Depends(get_crypto),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Localiza o usuário pelo Blind Index do e-mail e valida a senha com Argon2id + Pepper."""
    email_bidx = crypto.blind_index.compute_index("email", str(payload.email))
    user = await user_repo.get_by_email_blind_index(email_bidx)
    if user is None or not crypto.passwords.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    token = create_access_token(subject=user.id, settings=settings)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        user_id=user.id,
    )


@router.post(
    "/verify-password",
    response_model=PasswordVerifyResponse,
    summary="Verifica uma senha e exibe a decomposição do hash Argon2id + Salt + Pepper",
)
async def verify_password_demo(
    payload: PasswordVerifyRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    crypto: CryptoSuite = Depends(get_crypto),
) -> PasswordVerifyResponse:
    """Endpoint didático para testar a verificação de senha e inspecionar o PHC string do Argon2id."""
    email_bidx = crypto.blind_index.compute_index("email", str(payload.email))
    user = await user_repo.get_by_email_blind_index(email_bidx)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado para o e-mail informado.",
        )

    matched = crypto.passwords.verify_password(payload.password, user.password_hash)
    inspected = crypto.passwords.inspect_hash(user.password_hash)
    return PasswordVerifyResponse(
        matched=matched,
        user_id=user.id,
        algorithm=inspected.algorithm,
        argon2_version=inspected.version,
        argon2_parameters=inspected.parameters,
        salt_b64=inspected.salt_b64,
        hash_b64=inspected.hash_b64,
        uses_server_pepper=inspected.uses_server_pepper,
        stored_phc_string=inspected.raw_hash,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retorna os dados descriptografados do usuário autenticado via Bearer JWT",
)
async def get_me(
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Valida o Bearer Token JWT e retorna o perfil completo descriptografado."""
    return await user_service.get_user_by_id(current_user_id)

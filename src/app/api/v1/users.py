"""Rotas CRUD e busca cega (Blind Index) para Usuários (`User`)."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_user_service
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Usuários (PII Criptografada)"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um usuário criptografando PII, senha (Argon2id) e prontuário opcional",
)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Cadastra um novo usuário com chave exclusiva derivada via HKDF (Salt + Pepper)."""
    return await service.create_user(payload)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Lista os usuários cadastrados (descriptografados pela API)",
)
async def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """Retorna a lista paginada de usuários com seus dados descriptografados em tempo de execução."""
    return await service.list_users(limit=limit, offset=offset)


@router.get(
    "/search/by-email",
    response_model=UserResponse,
    summary="Busca usuário por e-mail usando Blind Index (HMAC-SHA256) sem descriptografar a tabela",
)
async def search_user_by_email(
    email: str = Query(..., description="E-mail exato a ser buscado via Blind Index."),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Calcula `HMAC-SHA256(pepper, email)` e executa `WHERE email_blind_index = ?` em O(1)."""
    return await service.search_by_email(email)


@router.get(
    "/search/by-cpf",
    response_model=UserResponse,
    summary="Busca usuário por CPF usando Blind Index (HMAC-SHA256) sem descriptografar a tabela",
)
async def search_user_by_cpf(
    cpf: str = Query(..., description="CPF (com ou sem pontuação) a ser buscado via Blind Index."),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Normaliza os 11 dígitos do CPF, calcula o Blind Index HMAC e busca em O(1)."""
    return await service.search_by_cpf(cpf)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtém um usuário pelo ID descriptografando seus dados e prontuário",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Recupera o registro pelo UUID e descriptografa usando a chave derivada do usuário."""
    return await service.get_user_by_id(user_id)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um usuário e seu prontuário médico",
)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> Response:
    """Exclui permanentemente o usuário e seu prontuário médico."""
    await service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""Serviço de domínio para gestão de Usuários, PII criptografada, Blind Index e senhas."""

import uuid

from fastapi import HTTPException, status

from app.core.crypto import CryptoSuite
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.medical_record_service import MedicalRecordService


class UserService:
    """Coordena criação, busca por Blind Index e descriptografia de `User`."""

    def __init__(
        self,
        user_repo: UserRepository,
        medical_service: MedicalRecordService,
        crypto: CryptoSuite,
    ) -> None:
        self._user_repo = user_repo
        self._medical_service = medical_service
        self._crypto = crypto

    def decrypt_to_response(self, user: User) -> UserResponse:
        """Descriptografa os campos pessoais (PII) e o prontuário médico se presente."""
        uid = user.id
        salt = user.user_salt
        fields = self._crypto.fields

        full_name = fields.decrypt_str(
            user.full_name_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="full_name",
        )
        email = fields.decrypt_str(
            user.email_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="email",
        )
        cpf = fields.decrypt_str(
            user.cpf_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="cpf",
        )

        med_resp = None
        if user.medical_record is not None:
            med_resp = self._medical_service.decrypt_to_response(user.medical_record, user)

        return UserResponse(
            id=user.id,
            full_name=full_name,
            email=email,
            cpf=cpf,
            created_at=user.created_at,
            updated_at=user.updated_at,
            medical_record=med_resp,
        )

    async def create_user(self, payload: UserCreate) -> UserResponse:
        """Cria um novo usuário criptografando PII, gerando Blind Indexes e hash Argon2id."""
        email_bidx = self._crypto.blind_index.compute_index("email", str(payload.email))
        cpf_bidx = self._crypto.blind_index.compute_index("cpf", payload.cpf)

        if await self._user_repo.get_by_email_blind_index(email_bidx) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este e-mail.",
            )
        if await self._user_repo.get_by_cpf_blind_index(cpf_bidx) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este CPF.",
            )

        user_id = str(uuid.uuid4())
        user_salt = self._crypto.fields.generate_user_salt()
        fields = self._crypto.fields

        user = User(
            id=user_id,
            user_salt=user_salt,
            email_blind_index=email_bidx,
            cpf_blind_index=cpf_bidx,
            full_name_encrypted=fields.encrypt_str(
                payload.full_name,
                user_id=user_id,
                user_salt=user_salt,
                field_name="full_name",
            ),
            email_encrypted=fields.encrypt_str(
                str(payload.email).lower(),
                user_id=user_id,
                user_salt=user_salt,
                field_name="email",
            ),
            cpf_encrypted=fields.encrypt_str(
                payload.cpf,
                user_id=user_id,
                user_salt=user_salt,
                field_name="cpf",
            ),
            password_hash=self._crypto.passwords.hash_password(payload.password),
        )

        if payload.medical_record is not None:
            user.medical_record = self._medical_service.build_encrypted_entity(
                user, payload.medical_record
            )

        created = await self._user_repo.create(user)
        return self.decrypt_to_response(created)

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Busca usuário por ID e retorna seus dados descriptografados."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        return self.decrypt_to_response(user)

    async def search_by_email(self, email: str) -> UserResponse:
        """Localiza um usuário em O(1) usando o Blind Index do e-mail."""
        email_bidx = self._crypto.blind_index.compute_index("email", email)
        user = await self._user_repo.get_by_email_blind_index(email_bidx)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum usuário encontrado para o e-mail informado.",
            )
        return self.decrypt_to_response(user)

    async def search_by_cpf(self, cpf: str) -> UserResponse:
        """Localiza um usuário em O(1) usando o Blind Index do CPF."""
        cpf_bidx = self._crypto.blind_index.compute_index("cpf", cpf)
        user = await self._user_repo.get_by_cpf_blind_index(cpf_bidx)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum usuário encontrado para o CPF informado.",
            )
        return self.decrypt_to_response(user)

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[UserResponse]:
        """Lista usuários descriptografando os dados para exibição na API."""
        users = await self._user_repo.list_all(limit=limit, offset=offset)
        return [self.decrypt_to_response(u) for u in users]

    async def delete_user(self, user_id: str) -> None:
        """Remove o usuário e seu prontuário médico do banco."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        await self._user_repo.delete(user)

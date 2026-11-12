"""Serviço de domínio para criptografia, persistência e leitura de Prontuários Médicos."""

import uuid

from fastapi import HTTPException, status

from app.core.crypto import CryptoSuite
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository
from app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordResponse,
    MedicalRecordUpdate,
)


class MedicalRecordService:
    """Coordena a criptografia por usuário e persistência de prontuários médicos."""

    def __init__(
        self,
        record_repo: MedicalRecordRepository,
        user_repo: UserRepository,
        crypto: CryptoSuite,
    ) -> None:
        self._record_repo = record_repo
        self._user_repo = user_repo
        self._crypto = crypto

    def build_encrypted_entity(
        self,
        user: User,
        payload: MedicalRecordCreate,
        record_id: str | None = None,
    ) -> MedicalRecord:
        """Constrói uma entidade `MedicalRecord` com todos os campos clínicos criptografados."""
        uid = user.id
        salt = user.user_salt
        fields = self._crypto.fields

        return MedicalRecord(
            id=record_id or str(uuid.uuid4()),
            user_id=uid,
            blood_type_blind_index=self._crypto.blind_index.compute_index(
                "blood_type", payload.blood_type
            ),
            weight_kg_encrypted=fields.encrypt_float(
                payload.weight_kg,
                user_id=uid,
                user_salt=salt,
                field_name="weight_kg",
            ),
            height_m_encrypted=fields.encrypt_float(
                payload.height_m,
                user_id=uid,
                user_salt=salt,
                field_name="height_m",
            ),
            blood_type_encrypted=fields.encrypt_str(
                payload.blood_type,
                user_id=uid,
                user_salt=salt,
                field_name="blood_type",
            ),
            allergies_encrypted=fields.encrypt_json(
                payload.allergies,
                user_id=uid,
                user_salt=salt,
                field_name="allergies",
            ),
            diagnoses_encrypted=fields.encrypt_json(
                payload.diagnoses,
                user_id=uid,
                user_salt=salt,
                field_name="diagnoses",
            ),
            medical_notes_encrypted=fields.encrypt_str(
                payload.medical_notes,
                user_id=uid,
                user_salt=salt,
                field_name="medical_notes",
            ),
        )

    def decrypt_to_response(
        self,
        record: MedicalRecord,
        user: User,
    ) -> MedicalRecordResponse:
        """Descriptografa todos os campos clínicos usando a chave derivada do usuário."""
        uid = user.id
        salt = user.user_salt
        fields = self._crypto.fields

        weight_kg = fields.decrypt_float(
            record.weight_kg_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="weight_kg",
        )
        height_m = fields.decrypt_float(
            record.height_m_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="height_m",
        )
        blood_type = fields.decrypt_str(
            record.blood_type_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="blood_type",
        )
        allergies = fields.decrypt_json(
            record.allergies_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="allergies",
        )
        diagnoses = fields.decrypt_json(
            record.diagnoses_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="diagnoses",
        )
        medical_notes = fields.decrypt_str(
            record.medical_notes_encrypted,
            user_id=uid,
            user_salt=salt,
            field_name="medical_notes",
        )

        bmi = round(weight_kg / (height_m**2), 2) if height_m > 0 else 0.0

        return MedicalRecordResponse(
            id=record.id,
            user_id=record.user_id,
            weight_kg=weight_kg,
            height_m=height_m,
            bmi=bmi,
            blood_type=blood_type,
            allergies=list(allergies),
            diagnoses=list(diagnoses),
            medical_notes=medical_notes,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    async def upsert_for_user(
        self,
        user_id: str,
        payload: MedicalRecordCreate,
    ) -> MedicalRecordResponse:
        """Cria ou substitui o prontuário médico de um usuário gerando novos nonces AES-GCM."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        existing = await self._record_repo.get_by_user_id(user_id)
        if existing is None:
            record = self.build_encrypted_entity(user, payload)
        else:
            fresh = self.build_encrypted_entity(user, payload, record_id=existing.id)
            existing.blood_type_blind_index = fresh.blood_type_blind_index
            existing.weight_kg_encrypted = fresh.weight_kg_encrypted
            existing.height_m_encrypted = fresh.height_m_encrypted
            existing.blood_type_encrypted = fresh.blood_type_encrypted
            existing.allergies_encrypted = fresh.allergies_encrypted
            existing.diagnoses_encrypted = fresh.diagnoses_encrypted
            existing.medical_notes_encrypted = fresh.medical_notes_encrypted
            record = existing

        saved = await self._record_repo.save(record)
        return self.decrypt_to_response(saved, user)

    async def update_partial(
        self,
        user_id: str,
        payload: MedicalRecordUpdate,
    ) -> MedicalRecordResponse:
        """Atualiza campos específicos de um prontuário re-criptografando com novos nonces."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        existing = await self._record_repo.get_by_user_id(user_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prontuário médico não encontrado para este usuário.",
            )

        current_decrypted = self.decrypt_to_response(existing, user)
        merged = MedicalRecordCreate(
            weight_kg=(
                payload.weight_kg if payload.weight_kg is not None else current_decrypted.weight_kg
            ),
            height_m=(
                payload.height_m if payload.height_m is not None else current_decrypted.height_m
            ),
            blood_type=(
                payload.blood_type
                if payload.blood_type is not None
                else current_decrypted.blood_type  # type: ignore[arg-type]
            ),
            allergies=(
                payload.allergies if payload.allergies is not None else current_decrypted.allergies
            ),
            diagnoses=(
                payload.diagnoses if payload.diagnoses is not None else current_decrypted.diagnoses
            ),
            medical_notes=(
                payload.medical_notes
                if payload.medical_notes is not None
                else current_decrypted.medical_notes
            ),
        )
        return await self.upsert_for_user(user_id, merged)

    async def get_by_user_id(self, user_id: str) -> MedicalRecordResponse:
        """Retorna o prontuário médico descriptografado de um usuário."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        record = await self._record_repo.get_by_user_id(user_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prontuário médico não encontrado para este usuário.",
            )
        return self.decrypt_to_response(record, user)

    async def search_by_blood_type(self, blood_type: str) -> list[MedicalRecordResponse]:
        """Busca prontuários pelo Blind Index do tipo sanguíneo e descriptografa os resultados."""
        b_index = self._crypto.blind_index.compute_index("blood_type", blood_type)
        records = await self._record_repo.find_by_blood_type_blind_index(b_index)
        return [self.decrypt_to_response(rec, rec.user) for rec in records if rec.user is not None]

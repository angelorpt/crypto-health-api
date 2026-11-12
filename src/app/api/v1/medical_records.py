"""Rotas para gerenciamento de Prontuários Médicos (`MedicalRecord`) criptografados."""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_medical_record_service
from app.schemas.medical_record import (
    BloodTypeLiteral,
    MedicalRecordCreate,
    MedicalRecordResponse,
    MedicalRecordUpdate,
)
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(
    prefix="/medical-records",
    tags=["Prontuários Médicos (Saúde Criptografada)"],
)


@router.put(
    "/user/{user_id}",
    response_model=MedicalRecordResponse,
    summary="Cria ou substitui o prontuário médico de um usuário (ex: peso 80.0 kg)",
)
async def upsert_medical_record(
    user_id: str,
    payload: MedicalRecordCreate,
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordResponse:
    """Criptografa todos os campos clínicos com a chave derivada do usuário e Nonce único."""
    return await service.upsert_for_user(user_id, payload)


@router.patch(
    "/user/{user_id}",
    response_model=MedicalRecordResponse,
    summary="Atualiza parcialmente o prontuário médico de um usuário",
)
async def patch_medical_record(
    user_id: str,
    payload: MedicalRecordUpdate,
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordResponse:
    """Atualiza apenas os campos enviados e re-criptografa o prontuário com novos nonces."""
    return await service.update_partial(user_id, payload)


@router.get(
    "/user/{user_id}",
    response_model=MedicalRecordResponse,
    summary="Obtém o prontuário médico descriptografado de um usuário",
)
async def get_medical_record_by_user(
    user_id: str,
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordResponse:
    """Descriptografa o prontuário médico do usuário e calcula o IMC em tempo real."""
    return await service.get_by_user_id(user_id)


@router.get(
    "/search/by-blood-type",
    response_model=list[MedicalRecordResponse],
    summary="Busca prontuários por Tipo Sanguíneo via Blind Index sem descriptografar a tabela inteira",
)
async def search_by_blood_type(
    blood_type: BloodTypeLiteral = Query(..., description="Tipo sanguíneo (ex: O+)."),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> list[MedicalRecordResponse]:
    """Usa o `blood_type_blind_index` (HMAC-SHA256) para filtrar registros antes de descriptografar."""
    return await service.search_by_blood_type(blood_type)

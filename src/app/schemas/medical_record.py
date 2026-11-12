"""Schemas de entrada e saída para Prontuários Médicos (`MedicalRecord`)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BloodTypeLiteral = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class MedicalRecordCreate(BaseModel):
    """Payload para criação ou atualização completa de um prontuário médico."""

    weight_kg: float = Field(
        ...,
        gt=0.5,
        le=500.0,
        examples=[80.0],
        description="Peso do paciente em quilogramas (ex: 80.0). Criptografado com AES-256-GCM por usuário.",
    )
    height_m: float = Field(
        ...,
        gt=0.3,
        le=2.8,
        examples=[1.75],
        description="Altura do paciente em metros (ex: 1.75). Criptografada com AES-256-GCM por usuário.",
    )
    blood_type: BloodTypeLiteral = Field(
        ...,
        examples=["O+"],
        description="Tipo sanguíneo (ABO/Rh). Criptografado + Blind Index para busca de doadores.",
    )
    allergies: list[str] = Field(
        default_factory=list,
        examples=[["Dipirona", "Penicilina"]],
        description="Lista de alergias (serializada em JSON e criptografada com AES-256-GCM).",
    )
    diagnoses: list[str] = Field(
        default_factory=list,
        examples=[["Hipertensão Arterial (CID I10)"]],
        description="Lista de diagnósticos/condições clínicas (criptografada com AES-256-GCM).",
    )
    medical_notes: str = Field(
        default="",
        max_length=5000,
        examples=["Paciente pratica atividade física regular; pressão controlada."],
        description="Observações médicas confidenciais (criptografadas com AES-256-GCM).",
    )


class MedicalRecordUpdate(BaseModel):
    """Payload para atualização parcial (PATCH/PUT) de prontuário médico."""

    weight_kg: float | None = Field(default=None, gt=0.5, le=500.0, examples=[80.0])
    height_m: float | None = Field(default=None, gt=0.3, le=2.8, examples=[1.75])
    blood_type: BloodTypeLiteral | None = Field(default=None, examples=["O+"])
    allergies: list[str] | None = Field(default=None)
    diagnoses: list[str] | None = Field(default=None)
    medical_notes: str | None = Field(default=None, max_length=5000)


class MedicalRecordResponse(BaseModel):
    """Prontuário médico descriptografado retornado pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    weight_kg: float
    height_m: float
    bmi: float = Field(..., description="IMC calculado dinamicamente após a descriptografia.")
    blood_type: str
    allergies: list[str]
    diagnoses: list[str]
    medical_notes: str
    created_at: datetime
    updated_at: datetime

"""Schemas de entrada e saída para Usuários e prontuário aninhado opcional."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordResponse


class UserCreate(BaseModel):
    """Payload para criação de um novo usuário com dados pessoais e prontuário opcional."""

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        examples=["Alice Souza"],
        description="Nome completo do usuário (será criptografado com AES-256-GCM).",
    )
    email: EmailStr = Field(
        ...,
        examples=["alice.souza@example.com"],
        description="E-mail do usuário (criptografado + Blind Index HMAC-SHA256 para busca).",
    )
    cpf: str = Field(
        ...,
        min_length=11,
        max_length=14,
        examples=["123.456.789-01"],
        description="CPF do usuário (normalizado, criptografado e indexado via Blind Index).",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        examples=["SenhaForte@123"],
        description="Senha em texto plano (transformada em hash irreversível Argon2id + Salt + Pepper).",
    )
    medical_record: MedicalRecordCreate | None = Field(
        default=None,
        description="Dados médicos opcionais já cadastrados junto com o usuário.",
    )

    @field_validator("cpf")
    @classmethod
    def validate_cpf_digits(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
        return digits


class UserResponse(BaseModel):
    """Resposta padrão com dados do usuário descriptografados de forma transparente pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID único do usuário.")
    full_name: str = Field(..., description="Nome completo descriptografado.")
    email: EmailStr = Field(..., description="E-mail descriptografado.")
    cpf: str = Field(..., description="CPF descriptografado.")
    created_at: datetime
    updated_at: datetime
    medical_record: MedicalRecordResponse | None = None

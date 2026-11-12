"""Schemas dedicados aos endpoints de Demonstração e Auditoria Criptográfica."""

from typing import Any

from pydantic import BaseModel, Field


class FieldCipherBreakdown(BaseModel):
    """Detalhamento completo de um único campo criptografado (visão Banco vs visão API)."""

    field_name: str
    plaintext_value: Any
    raw_database_value: str
    envelope_version: str
    nonce_b64: str
    nonce_hex: str
    ciphertext_b64: str
    ciphertext_hex: str
    gcm_auth_tag_b64: str
    gcm_auth_tag_hex: str
    aad_context: str
    blind_index_hmac_sha256: str | None = None


class UserCryptoInspectionResponse(BaseModel):
    """Inspeção completa de um usuário mostrando exatamente o que está salvo no banco vs texto plano."""

    user_id: str
    key_derivation_info: dict[str, Any]
    password_security: dict[str, Any]
    user_fields: dict[str, FieldCipherBreakdown]
    medical_fields: dict[str, FieldCipherBreakdown] | None = None


class IdenticalDataFieldComparison(BaseModel):
    """Comparação lado a lado de um mesmo campo (ex: peso 80.0 kg) entre dois usuários distintos."""

    field_name: str
    shared_plaintext_value: Any
    user_a_ciphertext: str
    user_a_nonce_hex: str
    user_a_aad: str
    user_b_ciphertext: str
    user_b_nonce_hex: str
    user_b_aad: str
    ciphertexts_are_different: bool
    why_different: str


class SeedComparisonResponse(BaseModel):
    """Resposta do endpoint que cria/compara dois pacientes com dados médicos 100% idênticos."""

    summary: str
    user_a_id: str
    user_a_salt: str
    user_a_derived_key_fingerprint: str
    user_b_id: str
    user_b_salt: str
    user_b_derived_key_fingerprint: str
    derived_keys_are_different: bool
    same_password_comparison: dict[str, Any]
    identical_medical_fields_comparison: list[IdenticalDataFieldComparison]


class TamperCheckRequest(BaseModel):
    """Parâmetros opcionais para simular um ataque de cópia/adulteração no banco."""

    source_user_id: str | None = Field(
        default=None,
        description="ID do usuário de origem (se omitido, usa o par de usuários da demo).",
    )
    target_user_id: str | None = Field(
        default=None,
        description="ID do usuário alvo onde o atacante tentaria colar o texto cifrado.",
    )


class TamperScenarioResult(BaseModel):
    """Resultado de um cenário de ataque contra a integridade/isolamento criptográfico."""

    scenario: str
    attack_description: str
    blocked_by_crypto: bool
    error_raised: str
    security_mechanism: str


class TamperCheckResponse(BaseModel):
    """Relatório completo de resistência a adulteração (AEAD AES-256-GCM + HKDF + AAD)."""

    all_attacks_blocked: bool
    scenarios: list[TamperScenarioResult]


class CryptoPlaygroundRequest(BaseModel):
    """Payload interativo para testar a criptografia de qualquer valor em tempo real."""

    sample_plaintext: str = Field(
        default="80.0",
        examples=["80.0"],
        description="Valor que será criptografado para dois usuários diferentes e duas vezes para o mesmo usuário.",
    )
    field_name: str = Field(
        default="weight_kg",
        examples=["weight_kg"],
        description="Nome do campo para compor o AAD e o Blind Index.",
    )
    sample_password: str = Field(
        default="SenhaForte@123",
        examples=["SenhaForte@123"],
        description="Senha de exemplo para demonstrar dois hashes Argon2id + Pepper distintos.",
    )


class CryptoPlaygroundResponse(BaseModel):
    """Resultado didático do playground criptográfico."""

    input_plaintext: str
    field_name: str
    user_1_simulation: dict[str, Any]
    user_2_simulation: dict[str, Any]
    same_user_second_encryption: dict[str, Any]
    blind_index_demo: dict[str, Any]
    password_hash_demo: dict[str, Any]
    proof_assertions: dict[str, bool]

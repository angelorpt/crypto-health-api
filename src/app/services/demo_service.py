"""Serviço de Demonstração e Auditoria Criptográfica.

Permite inspecionar valores brutos do banco, comparar dois usuários com dados médicos
100% iguais (ex: peso 80.0 kg, tipo O+, mesma senha) e provar que os textos cifrados
são totalmente distintos e protegidos contra adulteração (AEAD + HKDF + AAD).
"""

from typing import Any

from fastapi import HTTPException, status

from app.core.crypto import CryptoIntegrityError, CryptoSuite
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.demo import (
    CryptoPlaygroundRequest,
    CryptoPlaygroundResponse,
    FieldCipherBreakdown,
    IdenticalDataFieldComparison,
    SeedComparisonResponse,
    TamperCheckResponse,
    TamperScenarioResult,
    UserCryptoInspectionResponse,
)
from app.schemas.medical_record import MedicalRecordCreate
from app.schemas.user import UserCreate
from app.services.user_service import UserService

DEMO_USER_A_EMAIL = "alice.demo@example.com"
DEMO_USER_B_EMAIL = "bruno.demo@example.com"
DEMO_SHARED_PASSWORD = "MesmaSenhaDemo@2026"
DEMO_SHARED_MEDICAL = MedicalRecordCreate(
    weight_kg=80.0,
    height_m=1.75,
    blood_type="O+",
    allergies=["Dipirona", "Penicilina"],
    diagnoses=["Hipertensão Arterial (CID I10)"],
    medical_notes="Paciente com exatamente 80.0 kg e quadro clínico idêntico para demonstração.",
)


class DemoService:
    """Serviço especializado para provas visuais e técnicas da arquitetura de criptografia."""

    def __init__(
        self,
        user_repo: UserRepository,
        user_service: UserService,
        crypto: CryptoSuite,
    ) -> None:
        self._user_repo = user_repo
        self._user_service = user_service
        self._crypto = crypto

    def _build_field_breakdown(
        self,
        *,
        user_id: str,
        field_name: str,
        plaintext_value: Any,
        encrypted_token: str,
        blind_index: str | None = None,
    ) -> FieldCipherBreakdown:
        inspected = self._crypto.fields.inspect_token(
            encrypted_token,
            user_id=user_id,
            field_name=field_name,
        )
        return FieldCipherBreakdown(
            field_name=field_name,
            plaintext_value=plaintext_value,
            raw_database_value=inspected.raw_token,
            envelope_version=inspected.version,
            nonce_b64=inspected.nonce_b64,
            nonce_hex=inspected.nonce_hex,
            ciphertext_b64=inspected.ciphertext_b64,
            ciphertext_hex=inspected.ciphertext_hex,
            gcm_auth_tag_b64=inspected.auth_tag_b64,
            gcm_auth_tag_hex=inspected.auth_tag_hex,
            aad_context=inspected.aad_context,
            blind_index_hmac_sha256=blind_index,
        )

    async def inspect_user_crypto(self, user_id: str) -> UserCryptoInspectionResponse:
        """Retorna todos os valores brutos do banco (ciphertexts, nonces, tags, salts) vs texto plano."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado para inspeção.",
            )

        decrypted = self._user_service.decrypt_to_response(user)
        pwd_info = self._crypto.passwords.inspect_hash(user.password_hash)

        user_fields = {
            "full_name": self._build_field_breakdown(
                user_id=user.id,
                field_name="full_name",
                plaintext_value=decrypted.full_name,
                encrypted_token=user.full_name_encrypted,
            ),
            "email": self._build_field_breakdown(
                user_id=user.id,
                field_name="email",
                plaintext_value=str(decrypted.email),
                encrypted_token=user.email_encrypted,
                blind_index=user.email_blind_index,
            ),
            "cpf": self._build_field_breakdown(
                user_id=user.id,
                field_name="cpf",
                plaintext_value=decrypted.cpf,
                encrypted_token=user.cpf_encrypted,
                blind_index=user.cpf_blind_index,
            ),
        }

        medical_fields: dict[str, FieldCipherBreakdown] | None = None
        if user.medical_record is not None and decrypted.medical_record is not None:
            rec = user.medical_record
            d_med = decrypted.medical_record
            medical_fields = {
                "weight_kg": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="weight_kg",
                    plaintext_value=d_med.weight_kg,
                    encrypted_token=rec.weight_kg_encrypted,
                ),
                "height_m": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="height_m",
                    plaintext_value=d_med.height_m,
                    encrypted_token=rec.height_m_encrypted,
                ),
                "blood_type": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="blood_type",
                    plaintext_value=d_med.blood_type,
                    encrypted_token=rec.blood_type_encrypted,
                    blind_index=rec.blood_type_blind_index,
                ),
                "allergies": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="allergies",
                    plaintext_value=d_med.allergies,
                    encrypted_token=rec.allergies_encrypted,
                ),
                "diagnoses": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="diagnoses",
                    plaintext_value=d_med.diagnoses,
                    encrypted_token=rec.diagnoses_encrypted,
                ),
                "medical_notes": self._build_field_breakdown(
                    user_id=user.id,
                    field_name="medical_notes",
                    plaintext_value=d_med.medical_notes,
                    encrypted_token=rec.medical_notes_encrypted,
                ),
            }

        return UserCryptoInspectionResponse(
            user_id=user.id,
            key_derivation_info={
                "kdf_algorithm": "HKDF-SHA256",
                "aead_cipher": "AES-256-GCM (96-bit random nonce + 128-bit auth tag)",
                "user_salt_b64url": user.user_salt,
                "uses_server_encryption_pepper": True,
                "derived_dek_fingerprint": self._crypto.fields.derive_user_key_fingerprint(
                    user.user_salt
                ),
            },
            password_security={
                "algorithm": pwd_info.algorithm,
                "version": pwd_info.version,
                "parameters": pwd_info.parameters,
                "salt_b64": pwd_info.salt_b64,
                "hash_b64": pwd_info.hash_b64,
                "uses_server_password_pepper": pwd_info.uses_server_pepper,
                "raw_phc_string": pwd_info.raw_hash,
            },
            user_fields=user_fields,
            medical_fields=medical_fields,
        )

    async def _ensure_demo_users(self) -> tuple[User, User]:
        """Garante que os dois usuários de comparação (Alice e Bruno) existam com dados médicos idênticos."""
        bidx_a = self._crypto.blind_index.compute_index("email", DEMO_USER_A_EMAIL)
        bidx_b = self._crypto.blind_index.compute_index("email", DEMO_USER_B_EMAIL)

        user_a = await self._user_repo.get_by_email_blind_index(bidx_a)
        if user_a is None:
            created_a = await self._user_service.create_user(
                UserCreate(
                    full_name="Alice Demo (Paciente A - 80kg)",
                    email=DEMO_USER_A_EMAIL,
                    cpf="11122233344",
                    password=DEMO_SHARED_PASSWORD,
                    medical_record=DEMO_SHARED_MEDICAL,
                )
            )
            user_a = await self._user_repo.get_by_id(created_a.id)

        user_b = await self._user_repo.get_by_email_blind_index(bidx_b)
        if user_b is None:
            created_b = await self._user_service.create_user(
                UserCreate(
                    full_name="Bruno Demo (Paciente B - 80kg)",
                    email=DEMO_USER_B_EMAIL,
                    cpf="55566677788",
                    password=DEMO_SHARED_PASSWORD,
                    medical_record=DEMO_SHARED_MEDICAL,
                )
            )
            user_b = await self._user_repo.get_by_id(created_b.id)

        assert user_a is not None and user_b is not None
        return user_a, user_b

    async def seed_and_compare_identical_data(self) -> SeedComparisonResponse:
        """Cria/recupera dois usuários com os MESMOS dados médicos (ex: 80.0 kg) e compara os ciphertexts."""
        user_a, user_b = await self._ensure_demo_users()
        assert user_a.medical_record is not None and user_b.medical_record is not None

        rec_a = user_a.medical_record
        rec_b = user_b.medical_record

        fp_a = self._crypto.fields.derive_user_key_fingerprint(user_a.user_salt)
        fp_b = self._crypto.fields.derive_user_key_fingerprint(user_b.user_salt)

        field_pairs = [
            (
                "weight_kg",
                DEMO_SHARED_MEDICAL.weight_kg,
                rec_a.weight_kg_encrypted,
                rec_b.weight_kg_encrypted,
            ),
            (
                "height_m",
                DEMO_SHARED_MEDICAL.height_m,
                rec_a.height_m_encrypted,
                rec_b.height_m_encrypted,
            ),
            (
                "blood_type",
                DEMO_SHARED_MEDICAL.blood_type,
                rec_a.blood_type_encrypted,
                rec_b.blood_type_encrypted,
            ),
            (
                "allergies",
                DEMO_SHARED_MEDICAL.allergies,
                rec_a.allergies_encrypted,
                rec_b.allergies_encrypted,
            ),
            (
                "diagnoses",
                DEMO_SHARED_MEDICAL.diagnoses,
                rec_a.diagnoses_encrypted,
                rec_b.diagnoses_encrypted,
            ),
            (
                "medical_notes",
                DEMO_SHARED_MEDICAL.medical_notes,
                rec_a.medical_notes_encrypted,
                rec_b.medical_notes_encrypted,
            ),
        ]

        comparisons: list[IdenticalDataFieldComparison] = []
        for fname, shared_val, token_a, token_b in field_pairs:
            insp_a = self._crypto.fields.inspect_token(token_a, user_id=user_a.id, field_name=fname)
            insp_b = self._crypto.fields.inspect_token(token_b, user_id=user_b.id, field_name=fname)
            comparisons.append(
                IdenticalDataFieldComparison(
                    field_name=fname,
                    shared_plaintext_value=shared_val,
                    user_a_ciphertext=token_a,
                    user_a_nonce_hex=insp_a.nonce_hex,
                    user_a_aad=insp_a.aad_context,
                    user_b_ciphertext=token_b,
                    user_b_nonce_hex=insp_b.nonce_hex,
                    user_b_aad=insp_b.aad_context,
                    ciphertexts_are_different=(token_a != token_b),
                    why_different=(
                        "Chave DEK exclusiva por usuário via HKDF-SHA256(ServerPepper + UserSalt) "
                        "+ Nonce aleatório de 96 bits + AAD exclusivo (user_id + field_name)."
                    ),
                )
            )

        pwd_a = self._crypto.passwords.inspect_hash(user_a.password_hash)
        pwd_b = self._crypto.passwords.inspect_hash(user_b.password_hash)

        return SeedComparisonResponse(
            summary=(
                "Ambos os usuários possuem exatamente o mesmo peso (80.0 kg), altura (1.75 m), "
                "tipo sanguíneo (O+), alergias, diagnósticos e a mesma senha, mas 100% dos valores "
                "armazenados no banco de dados são criptograficamente distintos."
            ),
            user_a_id=user_a.id,
            user_a_salt=user_a.user_salt,
            user_a_derived_key_fingerprint=fp_a,
            user_b_id=user_b.id,
            user_b_salt=user_b.user_salt,
            user_b_derived_key_fingerprint=fp_b,
            derived_keys_are_different=(fp_a != fp_b),
            same_password_comparison={
                "shared_password_plaintext": DEMO_SHARED_PASSWORD,
                "user_a_password_hash": user_a.password_hash,
                "user_a_argon2_salt": pwd_a.salt_b64,
                "user_b_password_hash": user_b.password_hash,
                "user_b_argon2_salt": pwd_b.salt_b64,
                "hashes_are_different": user_a.password_hash != user_b.password_hash,
                "mechanism": "HMAC-SHA256(password, ServerPasswordPepper) -> Argon2id(random_16B_salt)",
            },
            identical_medical_fields_comparison=comparisons,
        )

    async def run_tamper_checks(
        self,
        source_user_id: str | None = None,
        target_user_id: str | None = None,
    ) -> TamperCheckResponse:
        """Executa 3 cenários de ataque provando que o banco não aceita cópia ou adulteração de ciphertexts."""
        if source_user_id and target_user_id:
            user_a = await self._user_repo.get_by_id(source_user_id)
            user_b = await self._user_repo.get_by_id(target_user_id)
            if not user_a or not user_b or not user_a.medical_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuários ou prontuário de origem não encontrados para teste de adulteração.",
                )
        else:
            user_a, user_b = await self._ensure_demo_users()

        assert user_a.medical_record is not None
        weight_cipher_a = user_a.medical_record.weight_kg_encrypted
        scenarios: list[TamperScenarioResult] = []

        # Cenário 1: Atacante copia o ciphertext de peso (80 kg) do Usuário A para o registro do Usuário B
        try:
            self._crypto.fields.decrypt_float(
                weight_cipher_a,
                user_id=user_b.id,
                user_salt=user_b.user_salt,
                field_name="weight_kg",
            )
            scenarios.append(
                TamperScenarioResult(
                    scenario="cross_user_ciphertext_transplant",
                    attack_description="Copiar `weight_kg_encrypted` do Usuário A para a linha do Usuário B.",
                    blocked_by_crypto=False,
                    error_raised="None",
                    security_mechanism="HKDF Per-User DEK + AES-GCM AAD",
                )
            )
        except CryptoIntegrityError as exc:
            scenarios.append(
                TamperScenarioResult(
                    scenario="cross_user_ciphertext_transplant",
                    attack_description=(
                        "Atacante com acesso ao banco copia o `weight_kg_encrypted` (80.0 kg) "
                        "do Usuário A e cola na coluna `weight_kg_encrypted` do Usuário B."
                    ),
                    blocked_by_crypto=True,
                    error_raised=str(exc),
                    security_mechanism=(
                        "Dupla proteção: (1) A chave DEK derivada via HKDF do Usuário B é diferente; "
                        "(2) O AAD exige `user:<user_b_id>|field:weight_kg`."
                    ),
                )
            )

        # Cenário 2: Atacante copia `weight_kg_encrypted` para a coluna `height_m_encrypted` do MESMO Usuário A
        try:
            self._crypto.fields.decrypt_float(
                weight_cipher_a,
                user_id=user_a.id,
                user_salt=user_a.user_salt,
                field_name="height_m",
            )
            scenarios.append(
                TamperScenarioResult(
                    scenario="same_user_cross_column_swap",
                    attack_description="Trocar `weight_kg_encrypted` para a coluna `height_m` do mesmo usuário.",
                    blocked_by_crypto=False,
                    error_raised="None",
                    security_mechanism="AES-GCM AAD field binding",
                )
            )
        except CryptoIntegrityError as exc:
            scenarios.append(
                TamperScenarioResult(
                    scenario="same_user_cross_column_swap",
                    attack_description=(
                        "Atacante copia `weight_kg_encrypted` do Usuário A e cola na coluna "
                        "`height_m_encrypted` do próprio Usuário A."
                    ),
                    blocked_by_crypto=True,
                    error_raised=str(exc),
                    security_mechanism=(
                        "Proteção por AAD (Associated Authenticated Data): a tag GCM foi autenticada "
                        "para `field:weight_kg` e rejeita leitura como `field:height_m`."
                    ),
                )
            )

        # Cenário 3: Adulteração de 1 byte no payload cifrado no banco (Bit-flipping attack)
        parts = weight_cipher_a.split("$")
        corrupted_payload = parts[2][:-2] + ("AA" if parts[2][-2:] != "AA" else "BB")
        corrupted_token = f"{parts[0]}${parts[1]}${corrupted_payload}"
        try:
            self._crypto.fields.decrypt_float(
                corrupted_token,
                user_id=user_a.id,
                user_salt=user_a.user_salt,
                field_name="weight_kg",
            )
            scenarios.append(
                TamperScenarioResult(
                    scenario="ciphertext_bit_flip_tampering",
                    attack_description="Modificar bytes do texto cifrado diretamente no banco de dados.",
                    blocked_by_crypto=False,
                    error_raised="None",
                    security_mechanism="AES-256-GCM 128-bit Authentication Tag",
                )
            )
        except CryptoIntegrityError as exc:
            scenarios.append(
                TamperScenarioResult(
                    scenario="ciphertext_bit_flip_tampering",
                    attack_description=(
                        "Atacante altera 1 byte do texto cifrado armazenado no banco de dados "
                        "(ataque de bit-flipping)."
                    ),
                    blocked_by_crypto=True,
                    error_raised=str(exc),
                    security_mechanism="Tag de Autenticação de 128 bits do AES-256-GCM (AEAD).",
                )
            )

        return TamperCheckResponse(
            all_attacks_blocked=all(s.blocked_by_crypto for s in scenarios),
            scenarios=scenarios,
        )

    def run_crypto_playground(self, payload: CryptoPlaygroundRequest) -> CryptoPlaygroundResponse:
        """Executa uma simulação em memória para qualquer valor informado pelo usuário."""
        user_1_id = "sim-user-001"
        user_2_id = "sim-user-002"
        salt_1 = self._crypto.fields.generate_user_salt()
        salt_2 = self._crypto.fields.generate_user_salt()

        cipher_u1_first = self._crypto.fields.encrypt_str(
            payload.sample_plaintext,
            user_id=user_1_id,
            user_salt=salt_1,
            field_name=payload.field_name,
        )
        cipher_u1_second = self._crypto.fields.encrypt_str(
            payload.sample_plaintext,
            user_id=user_1_id,
            user_salt=salt_1,
            field_name=payload.field_name,
        )
        cipher_u2 = self._crypto.fields.encrypt_str(
            payload.sample_plaintext,
            user_id=user_2_id,
            user_salt=salt_2,
            field_name=payload.field_name,
        )

        insp_u1_first = self._crypto.fields.inspect_token(
            cipher_u1_first, user_id=user_1_id, field_name=payload.field_name
        )
        insp_u1_second = self._crypto.fields.inspect_token(
            cipher_u1_second, user_id=user_1_id, field_name=payload.field_name
        )
        insp_u2 = self._crypto.fields.inspect_token(
            cipher_u2, user_id=user_2_id, field_name=payload.field_name
        )

        decrypted_u1 = self._crypto.fields.decrypt_str(
            cipher_u1_first,
            user_id=user_1_id,
            user_salt=salt_1,
            field_name=payload.field_name,
        )
        decrypted_u2 = self._crypto.fields.decrypt_str(
            cipher_u2,
            user_id=user_2_id,
            user_salt=salt_2,
            field_name=payload.field_name,
        )

        bidx_1 = self._crypto.blind_index.compute_index(
            payload.field_name, payload.sample_plaintext
        )
        bidx_2 = self._crypto.blind_index.compute_index(
            payload.field_name, payload.sample_plaintext
        )

        pwd_hash_1 = self._crypto.passwords.hash_password(payload.sample_password)
        pwd_hash_2 = self._crypto.passwords.hash_password(payload.sample_password)

        return CryptoPlaygroundResponse(
            input_plaintext=payload.sample_plaintext,
            field_name=payload.field_name,
            user_1_simulation={
                "user_id": user_1_id,
                "user_salt": salt_1,
                "derived_dek_fingerprint": self._crypto.fields.derive_user_key_fingerprint(salt_1),
                "ciphertext": cipher_u1_first,
                "nonce_hex": insp_u1_first.nonce_hex,
                "aad": insp_u1_first.aad_context,
                "decrypted_back": decrypted_u1,
            },
            user_2_simulation={
                "user_id": user_2_id,
                "user_salt": salt_2,
                "derived_dek_fingerprint": self._crypto.fields.derive_user_key_fingerprint(salt_2),
                "ciphertext": cipher_u2,
                "nonce_hex": insp_u2.nonce_hex,
                "aad": insp_u2.aad_context,
                "decrypted_back": decrypted_u2,
            },
            same_user_second_encryption={
                "explanation": (
                    "Mesmo para o MESMO usuário e MESMO valor, uma segunda gravação gera outro "
                    "ciphertext graças ao Nonce aleatório de 96 bits do AES-256-GCM."
                ),
                "ciphertext": cipher_u1_second,
                "nonce_hex": insp_u1_second.nonce_hex,
            },
            blind_index_demo={
                "purpose": "Permite buscar registros exatos via WHERE sem descriptografar a tabela.",
                "hmac_sha256_index_1": bidx_1,
                "hmac_sha256_index_2": bidx_2,
                "deterministic_for_search": bidx_1 == bidx_2,
            },
            password_hash_demo={
                "sample_password": payload.sample_password,
                "hash_1": pwd_hash_1,
                "hash_2": pwd_hash_2,
                "both_verify_true": (
                    self._crypto.passwords.verify_password(payload.sample_password, pwd_hash_1)
                    and self._crypto.passwords.verify_password(payload.sample_password, pwd_hash_2)
                ),
            },
            proof_assertions={
                "user_1_and_user_2_ciphertexts_differ": cipher_u1_first != cipher_u2,
                "same_user_two_writes_ciphertexts_differ": cipher_u1_first != cipher_u1_second,
                "both_decrypt_to_exact_input": (
                    decrypted_u1 == payload.sample_plaintext
                    and decrypted_u2 == payload.sample_plaintext
                ),
                "password_hashes_differ": pwd_hash_1 != pwd_hash_2,
                "blind_indexes_match_for_equality_search": bidx_1 == bidx_2,
            },
        )

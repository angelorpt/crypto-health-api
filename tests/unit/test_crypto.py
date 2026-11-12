"""Testes unitários exaustivos para o motor criptográfico (`app.core.crypto`)."""

import pytest

from app.core.crypto import (
    BlindIndexService,
    CryptoIntegrityError,
    FieldEncryptionService,
    PasswordCryptoService,
)


def test_same_weight_for_two_users_produces_completely_different_ciphertexts() -> None:
    """Garante que '80.0 kg' criptografado para dois usuários gere ciphertexts 100% distintos."""
    service = FieldEncryptionService("test-encryption-pepper-secret-123456")

    user_a_id = "user-a-uuid"
    user_b_id = "user-b-uuid"
    salt_a = service.generate_user_salt()
    salt_b = service.generate_user_salt()

    cipher_a = service.encrypt_float(
        80.0,
        user_id=user_a_id,
        user_salt=salt_a,
        field_name="weight_kg",
    )
    cipher_b = service.encrypt_float(
        80.0,
        user_id=user_b_id,
        user_salt=salt_b,
        field_name="weight_kg",
    )

    assert cipher_a != cipher_b
    assert service.derive_user_key(salt_a) != service.derive_user_key(salt_b)

    # Ambos descriptografam de volta para 80.0 exatamente
    assert (
        service.decrypt_float(
            cipher_a,
            user_id=user_a_id,
            user_salt=salt_a,
            field_name="weight_kg",
        )
        == 80.0
    )
    assert (
        service.decrypt_float(
            cipher_b,
            user_id=user_b_id,
            user_salt=salt_b,
            field_name="weight_kg",
        )
        == 80.0
    )


def test_same_user_encrypting_same_value_twice_produces_different_ciphertexts() -> None:
    """Garante criptografia probabilística (Nonce de 96 bits único por gravação)."""
    service = FieldEncryptionService("test-encryption-pepper-secret-123456")
    uid = "user-same-uuid"
    salt = service.generate_user_salt()

    c1 = service.encrypt_float(80.0, user_id=uid, user_salt=salt, field_name="weight_kg")
    c2 = service.encrypt_float(80.0, user_id=uid, user_salt=salt, field_name="weight_kg")

    assert c1 != c2
    assert service.decrypt_float(c1, user_id=uid, user_salt=salt, field_name="weight_kg") == 80.0
    assert service.decrypt_float(c2, user_id=uid, user_salt=salt, field_name="weight_kg") == 80.0


def test_cross_user_and_cross_field_tampering_is_rejected_by_aead() -> None:
    """Garante que copiar um ciphertext entre usuários ou entre colunas falha com CryptoIntegrityError."""
    service = FieldEncryptionService("test-encryption-pepper-secret-123456")
    salt_a = service.generate_user_salt()
    salt_b = service.generate_user_salt()

    cipher_weight_a = service.encrypt_float(
        80.0,
        user_id="user-a",
        user_salt=salt_a,
        field_name="weight_kg",
    )

    # Tentativa 1: Descriptografar no contexto do Usuário B
    with pytest.raises(CryptoIntegrityError):
        service.decrypt_float(
            cipher_weight_a,
            user_id="user-b",
            user_salt=salt_b,
            field_name="weight_kg",
        )

    # Tentativa 2: Descriptografar no mesmo Usuário A, mas como coluna `height_m` (AAD diferente)
    with pytest.raises(CryptoIntegrityError):
        service.decrypt_float(
            cipher_weight_a,
            user_id="user-a",
            user_salt=salt_a,
            field_name="height_m",
        )

    # Tentativa 3: Descriptografar com outro Pepper de servidor
    wrong_pepper_service = FieldEncryptionService("wrong-server-pepper-secret-999999")
    with pytest.raises(CryptoIntegrityError):
        wrong_pepper_service.decrypt_float(
            cipher_weight_a,
            user_id="user-a",
            user_salt=salt_a,
            field_name="weight_kg",
        )


def test_password_argon2id_plus_pepper_hashing_and_verification() -> None:
    """Garante que senhas iguais gerem hashes Argon2id diferentes e dependam do Pepper do servidor."""
    pwd_service = PasswordCryptoService("server-password-pepper-secret-abc")
    other_pepper_service = PasswordCryptoService("different-password-pepper-xyz")

    h1 = pwd_service.hash_password("MesmaSenha@123")
    h2 = pwd_service.hash_password("MesmaSenha@123")

    assert h1 != h2
    assert h1.startswith("$argon2id$")
    assert pwd_service.verify_password("MesmaSenha@123", h1) is True
    assert pwd_service.verify_password("MesmaSenha@123", h2) is True
    assert pwd_service.verify_password("SenhaErrada", h1) is False

    # Sem o Pepper correto do servidor, mesmo conhecendo a senha e o hash do banco, a verificação falha!
    assert other_pepper_service.verify_password("MesmaSenha@123", h1) is False


def test_blind_index_normalization_and_domain_separation() -> None:
    """Garante normalização de CPF/Email e separação de domínio entre colunas diferentes."""
    bidx = BlindIndexService("blind-index-pepper-secret-123456")

    # CPF formatado vs apenas números geram o mesmo Blind Index
    idx_cpf_formatted = bidx.compute_index("cpf", "123.456.789-01")
    idx_cpf_digits = bidx.compute_index("cpf", "12345678901")
    assert idx_cpf_formatted == idx_cpf_digits

    # E-mail com maiúsculas/espaços gera o mesmo Blind Index
    idx_email_upper = bidx.compute_index("email", "  Alice.Souza@Example.COM ")
    idx_email_lower = bidx.compute_index("email", "alice.souza@example.com")
    assert idx_email_upper == idx_email_lower

    # Mesmo valor bruto em campos diferentes gera Blind Indexes diferentes (separação de domínio)
    assert bidx.compute_index("cpf", "12345678901") != bidx.compute_index(
        "other_field", "12345678901"
    )

"""Motor criptográfico da aplicação (SOLID / Single Responsibility).

Implementa os três pilares da arquitetura de segurança de dados em repouso:
1. PasswordHasher (Irreversível):
   - Combina a senha com o `password_pepper` do servidor via HMAC-SHA256 e aplica
     `Argon2id` com Salt aleatório de 16 bytes por usuário.
2. BlindIndexer (Determinístico por Campo):
   - Normaliza campos pesquisáveis (CPF, e-mail, tipo sanguíneo) e gera um índice cego
     `HMAC-SHA256(blind_index_pepper, context:normalized_value)` para buscas exatas O(1)
     sem revelar o valor real no banco.
3. FieldEncryptor (Reversível, Probabilístico e Isolado por Usuário):
   - Deriva uma chave exclusiva de 256 bits (DEK) para cada usuário via `HKDF-SHA256`
     combinando o `encryption_pepper` (segredo de ambiente) com o `user_salt` (32 bytes
     únicos armazenados no registro do usuário).
   - Criptografa cada campo com `AES-256-GCM` usando um `nonce` aleatório de 96 bits (12 bytes)
     por operação e `AAD` (Associated Authenticated Data) vinculando `user_id:field_name`.
   - Resultado: dois usuários com peso `80.0 kg` possuem chaves derivadas diferentes, nonces
     diferentes, AADs diferentes e textos cifrados 100% diferentes, além de proteção contra
     adulteração ou troca de colunas no banco (InvalidTag).
"""

import base64
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from typing import Any

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import Settings, get_settings

ENVELOPE_VERSION = "v1"
NONCE_SIZE_BYTES = 12
GCM_TAG_SIZE_BYTES = 16
USER_SALT_SIZE_BYTES = 32
DEK_SIZE_BYTES = 32


class CryptoIntegrityError(Exception):
    """Exceção lançada quando a autenticação AEAD (AES-GCM) ou formato do token falha."""


@dataclass(frozen=True)
class CiphertextInspection:
    """Estrutura detalhada que decompõe um campo criptografado para fins de auditoria/demo."""

    raw_token: str
    version: str
    nonce_b64: str
    nonce_hex: str
    ciphertext_b64: str
    ciphertext_hex: str
    auth_tag_b64: str
    auth_tag_hex: str
    aad_context: str


@dataclass(frozen=True)
class PasswordHashInspection:
    """Estrutura detalhada que decompõe um hash Argon2id (formato PHC) para a demo."""

    raw_hash: str
    algorithm: str
    version: str
    parameters: str
    salt_b64: str
    hash_b64: str
    uses_server_pepper: bool


def _b64url_encode(data: bytes) -> str:
    """Codifica bytes em Base64 URL-safe sem padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Decodifica Base64 URL-safe restaurando o padding necessário."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


class PasswordCryptoService:
    """Serviço de hash irreversível de senhas utilizando Argon2id + Salt + Server Pepper."""

    def __init__(self, password_pepper: str) -> None:
        if not password_pepper:
            raise ValueError("O password_pepper não pode ser vazio.")
        self._pepper_bytes = password_pepper.encode("utf-8")
        # Parâmetros seguros e ágeis para API/Demo (RFC 9106 / OWASP)
        self._argon2 = Argon2Hasher(
            time_cost=2,
            memory_cost=19456,  # 19 MiB
            parallelism=2,
            hash_len=32,
            salt_len=16,
        )

    def _peppered_secret(self, plain_password: str) -> bytes:
        """Aplica HMAC-SHA256 com o Pepper do servidor antes de entregar ao Argon2id."""
        return hmac.new(
            self._pepper_bytes,
            plain_password.encode("utf-8"),
            hashlib.sha256,
        ).digest()

    def hash_password(self, plain_password: str) -> str:
        """Gera hash Argon2id com salt único aleatório + pepper do servidor."""
        peppered = self._peppered_secret(plain_password)
        return self._argon2.hash(peppered)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verifica se a senha em texto plano corresponde ao hash Argon2id armazenado."""
        peppered = self._peppered_secret(plain_password)
        try:
            return self._argon2.verify(password_hash, peppered)
        except (VerifyMismatchError, Exception):
            return False

    @staticmethod
    def inspect_hash(password_hash: str) -> PasswordHashInspection:
        """Decompõe uma string PHC do Argon2id (`$argon2id$v=19$m=...,t=...,p=...$salt$hash`)."""
        parts = password_hash.split("$")
        if len(parts) < 6:
            return PasswordHashInspection(
                raw_hash=password_hash,
                algorithm="unknown",
                version="unknown",
                parameters="",
                salt_b64="",
                hash_b64="",
                uses_server_pepper=True,
            )
        return PasswordHashInspection(
            raw_hash=password_hash,
            algorithm=parts[1],
            version=parts[2],
            parameters=parts[3],
            salt_b64=parts[4],
            hash_b64=parts[5],
            uses_server_pepper=True,
        )


class BlindIndexService:
    """Serviço de geração de Blind Indexes (HMAC-SHA256 + Pepper) para buscas exatas."""

    def __init__(self, blind_index_pepper: str) -> None:
        if not blind_index_pepper:
            raise ValueError("O blind_index_pepper não pode ser vazio.")
        self._pepper_bytes = blind_index_pepper.encode("utf-8")

    @staticmethod
    def normalize(field_name: str, value: str) -> str:
        """Normaliza o valor conforme o tipo do campo para garantir consistência de busca."""
        cleaned = value.strip()
        if field_name == "cpf":
            return re.sub(r"\D", "", cleaned)
        if field_name == "email":
            return cleaned.lower()
        if field_name == "blood_type":
            return cleaned.upper()
        return cleaned.lower()

    def compute_index(self, field_name: str, value: str) -> str:
        """Calcula o HMAC-SHA256 determinístico com separação de domínio por `field_name`."""
        normalized = self.normalize(field_name, value)
        domain_input = f"{field_name}:{normalized}".encode()
        return hmac.new(self._pepper_bytes, domain_input, hashlib.sha256).hexdigest()


class FieldEncryptionService:
    """Serviço de criptografia autenticada por campo (HKDF por usuário + AES-256-GCM + AAD)."""

    def __init__(self, encryption_pepper: str) -> None:
        if not encryption_pepper:
            raise ValueError("O encryption_pepper não pode ser vazio.")
        self._pepper_bytes = encryption_pepper.encode("utf-8")

    @staticmethod
    def generate_user_salt() -> str:
        """Gera um Salt criptográfico exclusivo de 32 bytes para um novo usuário."""
        return _b64url_encode(os.urandom(USER_SALT_SIZE_BYTES))

    def derive_user_key(self, user_salt: str) -> bytes:
        """Deriva uma chave DEK de 256 bits para o usuário via HKDF-SHA256(Pepper + User Salt)."""
        salt_bytes = _b64url_decode(user_salt)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=DEK_SIZE_BYTES,
            salt=salt_bytes,
            info=b"medvault-aes256gcm-user-dek-v1",
        )
        return hkdf.derive(self._pepper_bytes)

    def derive_user_key_fingerprint(self, user_salt: str) -> str:
        """Retorna um fingerprint seguro (SHA-256 truncado) da chave derivada apenas para exibição na demo."""
        dek = self.derive_user_key(user_salt)
        digest = hashlib.sha256(b"fingerprint:" + dek).hexdigest()
        return f"sha256:{digest[:16]}...{digest[-8:]}"

    @staticmethod
    def build_aad(user_id: str, field_name: str) -> bytes:
        """Constrói o Associated Authenticated Data vinculando o registro ao usuário e coluna."""
        return f"user:{user_id}|field:{field_name}".encode()

    def encrypt_str(
        self,
        plaintext: str,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> str:
        """Criptografa uma string em um envelope `v1$<nonce_b64url>$<ciphertext_tag_b64url>`."""
        dek = self.derive_user_key(user_salt)
        aesgcm = AESGCM(dek)
        nonce = os.urandom(NONCE_SIZE_BYTES)
        aad = self.build_aad(user_id, field_name)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return f"{ENVELOPE_VERSION}${_b64url_encode(nonce)}${_b64url_encode(ciphertext_with_tag)}"

    def decrypt_str(
        self,
        encrypted_token: str,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> str:
        """Descriptografa e valida autenticidade/integridade (GCM Tag + AAD + chave HKDF)."""
        try:
            parts = encrypted_token.split("$")
            if len(parts) != 3 or parts[0] != ENVELOPE_VERSION:
                raise CryptoIntegrityError("Formato ou versão de envelope criptográfico inválido.")
            nonce = _b64url_decode(parts[1])
            ciphertext_with_tag = _b64url_decode(parts[2])
        except CryptoIntegrityError:
            raise
        except Exception as exc:
            raise CryptoIntegrityError("Token criptográfico malformado.") from exc

        dek = self.derive_user_key(user_salt)
        aesgcm = AESGCM(dek)
        aad = self.build_aad(user_id, field_name)
        try:
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, aad)
            return plaintext_bytes.decode("utf-8")
        except InvalidTag as exc:
            raise CryptoIntegrityError(
                "Falha de autenticação AES-256-GCM (InvalidTag): chave incorreta, "
                "ciphertext adulterado ou tentativa de copiar dado entre usuários/campos diferentes (AAD mismatch)."
            ) from exc

    def encrypt_float(
        self,
        value: float,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> str:
        """Serializa e criptografa um número de ponto flutuante (ex: peso 80.0 kg)."""
        return self.encrypt_str(
            f"{value:.2f}",
            user_id=user_id,
            user_salt=user_salt,
            field_name=field_name,
        )

    def decrypt_float(
        self,
        encrypted_token: str,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> float:
        """Descriptografa e converte de volta para float."""
        raw = self.decrypt_str(
            encrypted_token,
            user_id=user_id,
            user_salt=user_salt,
            field_name=field_name,
        )
        return float(raw)

    def encrypt_json(
        self,
        data: Any,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> str:
        """Serializa estruturas JSON (ex: listas de alergias ou diagnósticos) e criptografa."""
        serialized = json.dumps(data, ensure_ascii=False)
        return self.encrypt_str(
            serialized,
            user_id=user_id,
            user_salt=user_salt,
            field_name=field_name,
        )

    def decrypt_json(
        self,
        encrypted_token: str,
        *,
        user_id: str,
        user_salt: str,
        field_name: str,
    ) -> Any:
        """Descriptografa e reconstrói a estrutura JSON original."""
        raw = self.decrypt_str(
            encrypted_token,
            user_id=user_id,
            user_salt=user_salt,
            field_name=field_name,
        )
        return json.loads(raw)

    def inspect_token(
        self,
        encrypted_token: str,
        *,
        user_id: str,
        field_name: str,
    ) -> CiphertextInspection:
        """Extrai os metadados criptográficos (nonce, corpo cifrado, tag GCM e AAD) para a Demo."""
        parts = encrypted_token.split("$")
        if len(parts) != 3:
            raise CryptoIntegrityError("Token inválido para inspeção.")
        version, nonce_b64, payload_b64 = parts
        nonce_bytes = _b64url_decode(nonce_b64)
        payload_bytes = _b64url_decode(payload_b64)
        ciphertext_bytes = payload_bytes[:-GCM_TAG_SIZE_BYTES]
        tag_bytes = payload_bytes[-GCM_TAG_SIZE_BYTES:]
        aad_str = self.build_aad(user_id, field_name).decode("utf-8")

        return CiphertextInspection(
            raw_token=encrypted_token,
            version=version,
            nonce_b64=nonce_b64,
            nonce_hex=nonce_bytes.hex(),
            ciphertext_b64=_b64url_encode(ciphertext_bytes),
            ciphertext_hex=ciphertext_bytes.hex(),
            auth_tag_b64=_b64url_encode(tag_bytes),
            auth_tag_hex=tag_bytes.hex(),
            aad_context=aad_str,
        )


@dataclass(frozen=True)
class CryptoSuite:
    """Fachada (Facade Pattern) agrupando os três serviços criptográficos da aplicação."""

    passwords: PasswordCryptoService
    blind_index: BlindIndexService
    fields: FieldEncryptionService


def build_crypto_suite(settings: Settings | None = None) -> CryptoSuite:
    """Constrói a suíte criptográfica a partir das configurações ativas."""
    cfg = settings or get_settings()
    return CryptoSuite(
        passwords=PasswordCryptoService(cfg.app_password_pepper),
        blind_index=BlindIndexService(cfg.app_blind_index_pepper),
        fields=FieldEncryptionService(cfg.app_encryption_pepper),
    )

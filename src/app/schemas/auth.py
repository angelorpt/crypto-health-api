"""Schemas de autenticação (Login JWT e Verificação de Senha Argon2id + Pepper)."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credenciais de login via e-mail (buscado por Blind Index) e senha."""

    email: EmailStr = Field(..., examples=["alice.souza@example.com"])
    password: str = Field(..., examples=["SenhaForte@123"])


class TokenResponse(BaseModel):
    """Token JWT emitido após verificação bem-sucedida da senha com Argon2id + Pepper."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: str


class PasswordVerifyRequest(BaseModel):
    """Payload para verificar uma senha contra um usuário e inspecionar os parâmetros Argon2id."""

    email: EmailStr = Field(..., examples=["alice.souza@example.com"])
    password: str = Field(..., examples=["SenhaForte@123"])


class PasswordVerifyResponse(BaseModel):
    """Resultado detalhado da verificação de senha demonstrando Argon2id + Salt + Pepper."""

    matched: bool
    user_id: str
    algorithm: str
    argon2_version: str
    argon2_parameters: str
    salt_b64: str
    hash_b64: str
    uses_server_pepper: bool
    stored_phc_string: str

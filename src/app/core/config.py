"""Configurações centralizadas da aplicação via variáveis de ambiente (12-Factor App)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais carregadas do ambiente ou arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="MedVault Crypto API")
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # Banco de Dados (suporta PostgreSQL asyncpg no Docker ou SQLite aiosqlite local/testes)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./medvault_demo.db",
        description="URL de conexão assíncrona do SQLAlchemy 2.0",
    )

    # Segredos criptográficos (Peppers do servidor - nunca armazenados no banco)
    app_encryption_pepper: str = Field(
        default="demo-master-encryption-pepper-change-in-prod-9f8e7d6c5b4a3210",
        min_length=16,
        description="Pepper mestre do servidor usado no HKDF para derivar chaves por usuário",
    )
    app_password_pepper: str = Field(
        default="demo-password-secret-pepper-change-in-prod-1a2b3c4d5e6f7a8b",
        min_length=16,
        description="Pepper secreto aplicado via HMAC antes do hash Argon2id de senhas",
    )
    app_blind_index_pepper: str = Field(
        default="demo-blind-index-pepper-change-in-prod-7f6e5d4c3b2a1908",
        min_length=16,
        description="Pepper secreto para geração de Blind Indexes determinísticos (HMAC-SHA256)",
    )

    # JWT
    jwt_secret_key: str = Field(
        default="demo-jwt-secret-key-change-in-production-32bytes-minimum",
        min_length=16,
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)


@lru_cache
def get_settings() -> Settings:
    """Retorna instância singleton em cache das configurações."""
    return Settings()

"""Ponto de entrada principal da aplicação FastAPI (MedVault Crypto API)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import __version__
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Gerencia o ciclo de vida da aplicação (inicialização de tabelas e encerramento do pool)."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Factory function (KISS / Testability) que instancia e configura a aplicação FastAPI."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API Demo focada em **Criptografia de Dados Sensíveis (PII & Prontuários Médicos)** "
            "no Banco de Dados.\n\n"
            "### Arquitetura Criptográfica\n"
            "- **Campos Sensíveis (Peso, Altura, Sangue, Diagnósticos, Alergias, Nome, CPF, E-mail)**: "
            "`AES-256-GCM` (AEAD) com Nonce aleatório de 96 bits, `AAD` (`user_id` + `field_name`) "
            "e chave exclusiva por usuário derivada via `HKDF-SHA256(ServerPepper + UserSalt)`.\n"
            "- **Buscas Exatas sem Descriptografar o Banco (CPF, E-mail, Tipo Sanguíneo)**: "
            "`Blind Index` com `HMAC-SHA256(ServerBlindIndexPepper, field:normalized_value)`.\n"
            "- **Senhas**: `HMAC-SHA256(password, ServerPasswordPepper)` + `Argon2id` com Salt único de 16 bytes."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_v1_router)

    @application.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        """Redireciona a raiz `/` para a documentação interativa `/docs`."""
        return RedirectResponse(url="/docs")

    return application


app = create_app()

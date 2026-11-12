# Diagrama C4: Nível 2 — Containers

> **Visão dos subsistemas executáveis, tecnologias, protocolos de rede e armazenamento de dados.**

Este diagrama descreve a arquitetura de containers do MedVault Crypto API utilizando o modelo C4 (Nível 2).

```mermaid
flowchart TB
    Client["📱 Navegador Web / Swagger UI / Futuro Front-end<br/>[Client HTTP / Single Page App]"]

    subgraph Host["Servidor / Ambiente de Execução da Aplicação"]
        subgraph DockerApp["Container / Processo: medvault-api"]
            Uvicorn["🚀 Uvicorn ASGI Server<br/>[Porta 8000]"]
            FastAPI["⚡ Framework FastAPI<br/>[Python 3.11+]"]
            CryptoEngine["🔐 Motor Criptográfico Puro<br/>[src/app/core/crypto.py]<br/>HKDF-SHA256, AES-256-GCM, HMAC, Argon2id"]
            Alembic["🔄 Alembic Migration Runner<br/>[Migrações assíncronas do schema]"]
        end

        subgraph Environment["Variáveis de Ambiente / Secret Store"]
            Peppers["🌶️ Peppers em Memória<br/>APP_ENCRYPTION_PEPPER<br/>APP_BLIND_INDEX_PEPPER<br/>APP_PASSWORD_PEPPER"]
        end

        subgraph DockerDB["Container / Processo: medvault-postgres"]
            Postgres[("🐘 PostgreSQL 16 / SQLite Async<br/>[Porta 5432 / Arquivo local]<br/>Tabelas: users, medical_records")]
        end
    end

    Client -->|HTTPS / JSON REST API| Uvicorn
    Uvicorn --> FastAPI
    FastAPI -->|Orquestração de Regras| CryptoEngine
    CryptoEngine -->|Lê segredos em memória| Peppers
    FastAPI -->|Queries SQL com ciphertexts via Asyncpg / Aiosqlite| Postgres
    Alembic -->|Aplica DDL inicial| Postgres

    classDef client fill:#1E88E5,stroke:#0D47A1,stroke-width:2px,color:#fff;
    classDef app fill:#43A047,stroke:#1B5E20,stroke-width:2px,color:#fff;
    classDef internal fill:#2E7D32,stroke:#1B5E20,stroke-width:2px,color:#fff;
    classDef secret fill:#FB8C00,stroke:#E65100,stroke-width:2px,color:#fff;
    classDef db fill:#3949AB,stroke:#1A237E,stroke-width:2px,color:#fff;

    class Client client;
    class DockerApp app;
    class Uvicorn,FastAPI,CryptoEngine,Alembic internal;
    class Peppers secret;
    class Postgres db;
```

---

### O que este nível explica:
1. **Frontend / Swagger** comunica-se via JSON HTTP com o servidor Uvicorn.
2. O **Motor Criptográfico** é executado dentro do processo da API Python, consumindo diretamente as bibliotecas `cryptography` e `argon2-cffi`.
3. Os **Peppers** residem estritamente na memória do processo da aplicação (`pydantic-settings`).
4. O **Banco de Dados** recebe apenas dados cifrados e os índices cegos gerados pelo motor antes do envio via SQLAlchemy Async.

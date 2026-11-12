# AGENTS.md — Guia Operacional para Agentes de IA / LLMs

Bem-vindo ao repositório **MedVault Crypto API** (`crypto-health-api`). Este arquivo é a fonte de verdade para qualquer Agente de IA ou assistente de codificação operando neste projeto.

---

## 1. Visão Geral e Contexto do Repositório

- **Escopo deste Repositório**: Exclusivamente o **Backend em Python (FastAPI + SQLAlchemy 2.0 Async)**. Futuramente, este repositório será incluído como um *git submodule* dentro de um repositório *umbrella* maior ao lado de um repositório Front-end separado.
- **Objetivo de Negócio**: Demonstrar criptografia de dados pessoais (**PII**) e prontuários médicos (**PHI**) no banco de dados garantindo que **dados idênticos (ex: dois pacientes com peso `80.0 kg` ou tipo sanguíneo `O+`) gerem textos cifrados 100% diferentes no banco**, continuem **descriptografáveis pela API** e suportem **buscas exatas em $O(1)$ via Blind Index**.

---

## 2. Convenção de Idioma

- **Código-Fonte, Variáveis, Tabelas, Colunas e Rotas HTTP**: **Inglês** (ex: `weight_kg`, `blood_type_encrypted`, `/api/v1/users`, `/api/v1/medical-records`).
- **Documentação, Docstrings, Descrições do OpenAPI/Swagger, Mensagens de Erro e Especificações**: **Português (PT-BR)**.

---

## 3. Catálogo de Scripts (`scripts/`) — Use Sempre Estes Comandos!

Todos os fluxos operacionais foram automatizados em `scripts/`. Sempre execute-os a partir da raiz do projeto (`/home/user/projects/cripto`) usando `bash scripts/<script>.sh`:

| Script | Comando | O que faz | Quando a IA deve usar |
| :--- | :--- | :--- | :--- |
| **Setup do Ambiente** | `bash scripts/setup.sh` | Cria a `.venv`, instala dependências (`pip install -e ".[dev]"`) e gera `.env` a partir de `.env.example`. | Na primeira execução ou ao adicionar dependências no `pyproject.toml`. |
| **Rodar Testes + Coverage** | `bash scripts/test.sh` | Executa `pytest -v --cov=src/app --cov-report=term-missing` usando SQLite assíncrono em memória (não depende de Docker). | **Obrigatório** após qualquer alteração de código em `src/` ou `tests/`. |
| **Verificar Lint & Estilo** | `bash scripts/lint.sh` | Executa `ruff check` e `ruff format --check` em `src`, `tests` e `scripts`. | Antes de concluir qualquer tarefa para garantir zero erros de lint/formatação. |
| **Formatar Código** | `bash scripts/format.sh` | Executa `ruff check --fix` e `ruff format` automaticamente. | Sempre que `lint.sh` apontar desvios de estilo ou ordenação de imports. |
| **Subir Servidor Dev Local** | `bash scripts/dev.sh` | Inicia o FastAPI (`uvicorn app.main:app --reload`) na porta `8000` usando a `.venv`. | Para testar a API localmente sem Docker. |
| **Subir Docker Compose** | `bash scripts/up.sh` | Sobe PostgreSQL 16 (`db`) + API (`api`) via `docker compose up -d --build` e aguarda o healthcheck `/api/v1/health`. | Quando o usuário pedir para subir os containers ou testar com PostgreSQL. |
| **Derrubar Docker Compose** | `bash scripts/down.sh` | Para e remove os containers (`bash scripts/down.sh -v` também apaga os volumes do Postgres). | Para encerrar serviços em background ou resetar o banco Docker. |
| **Ver Logs do Docker** | `bash scripts/logs.sh` | Exibe os logs recentes dos containers (`docker compose logs`). | Para diagnosticar falhas de inicialização ou migração nos containers. |
| **Rodar Migrações** | `bash scripts/migrate.sh` | Executa `alembic upgrade head` no banco configurado em `DATABASE_URL`. | Ao alterar modelos em `src/app/models/`. |
| **Cenário Demo & Inspecionar DB** | `bash scripts/demo-scenario.sh` | Executa `scripts/inspect_db.py`, criando dois pacientes com `80.0 kg` e imprimindo no terminal a prova JSON (ciphertexts distintos + bloqueio de adulteração). | Para demonstrar rapidamente o funcionamento criptográfico via CLI. |
| **Limpeza de Artefatos** | `bash scripts/clean.sh` | Remove `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.coverage` e banco SQLite local (`medvault_demo.db`). | Para limpar o workspace antes de commits ou rebuilds. |

---

## 4. Arquitetura em Camadas (`src/app/`) e Princípios (SOLID, DRY, KISS)

```text
src/app/
├── core/
│   ├── config.py       # Settings (pydantic-settings) lendo variáveis de ambiente e Peppers
│   ├── crypto.py       # Motor criptográfico PURO (HKDF + AES-256-GCM + AAD, HMAC Blind Index, Argon2id)
│   ├── database.py     # AsyncEngine e AsyncSession do SQLAlchemy 2.0
│   └── security.py     # Emissão e validação de tokens JWT (PyJWT)
├── models/
│   ├── user.py             # Tabela `users` (*_encrypted, *_blind_index, user_salt, password_hash)
│   └── medical_record.py   # Tabela `medical_records` (*_encrypted, blood_type_blind_index)
├── schemas/            # Contratos Pydantic v2 (user, medical_record, auth, demo)
├── repositories/       # Acesso a dados isolado (UserRepository, MedicalRecordRepository)
├── services/           # Regras de negócio e orquestração criptográfica (UserService, MedicalRecordService, DemoService)
├── api/
│   ├── deps.py         # Injeção de dependências FastAPI
│   └── v1/             # Routers REST (health, auth, users, medical_records, demo)
└── main.py             # Application Factory (`create_app()`)
```

---

## 5. Invariantes de Segurança (NUNCA Viole Estas Regras!)

1. **Nunca salve os Peppers no banco de dados**: `APP_ENCRYPTION_PEPPER`, `APP_PASSWORD_PEPPER` e `APP_BLIND_INDEX_PEPPER` devem vir exclusivamente de variáveis de ambiente (`Settings`).
2. **Nunca use Hash irreversível para campos que precisam ser lidos de volta**: Senhas usam `PasswordCryptoService` (`Argon2id` + Salt + Pepper). Dados médicos (`weight_kg`, `height_m`, `blood_type`, `allergies`, `diagnoses`, `medical_notes`) e PII (`full_name`, `email`, `cpf`) usam `FieldEncryptionService` (`HKDF-SHA256` por usuário + `AES-256-GCM` com Nonce aleatório de 96 bits).
3. **Sempre vincule o AAD no AES-256-GCM**: Toda chamada de criptografia/descriptografia de campo deve informar `user_id` e `field_name` para compor o Associated Authenticated Data (`user:{user_id}|field:{field_name}`). Isso impede ataques de cópia de texto cifrado entre usuários ou entre colunas.
4. **Buscas exatas usam Blind Index**: Nunca faça scan completo descriptografando a tabela para buscar por CPF, e-mail ou tipo sanguíneo; use `BlindIndexService.compute_index(field_name, value)`.

---

## 6. Documentação e OpenSpec

- Documentação executiva, didática e técnica em `docs/`:
  - [`docs/guia-didatico-criptografia.md`](docs/guia-didatico-criptografia.md) (Glossário visual, analogias, Threat Model e roteiro de Live Demo)
  - [`docs/apresentacao-slides.md`](docs/apresentacao-slides.md) (Deck de slides em Markdown/Marp ensinando cada conceito)
  - [`docs/one-pager.md`](docs/one-pager.md)
  - [`docs/prd.md`](docs/prd.md)
  - [`docs/adr/`](docs/adr/) (ADRs 0001 a 0004)
- Especificações vivas em `openspec/specs/`:
  - [`openspec/specs/crypto-engine/spec.md`](openspec/specs/crypto-engine/spec.md)
  - [`openspec/specs/medical-vault-api/spec.md`](openspec/specs/medical-vault-api/spec.md)

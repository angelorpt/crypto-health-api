# Guia Operacional: Como Executar o MedVault Crypto API Manualmente

> **Guia completo e autônomo para desenvolvedores. Não depende de scripts automatizados (`scripts/*.sh`).**

Este documento detalha **como configurar, executar, testar e auditar** o MedVault Crypto API passo a passo em qualquer ambiente Linux/macOS ou WSL, escolhendo entre SQLite local, PostgreSQL em container ou Docker Compose completo.

---

## 📋 Pré-requisitos do Sistema

| Ferramenta | Versão Mínima | Finalidade |
| :--- | :--- | :--- |
| **Python** | `3.11+` (recomendado `3.12`) | Interpretador principal da API |
| **Git** | `2.30+` | Versionamento de código |
| **Docker & Docker Compose** *(opcional)* | Docker 24+, Compose v2+ | Apenas para os cenários com PostgreSQL containerizado |
| **sqlite3** / **psql** *(opcional)* | Qualquer versão | Utilitários de linha de comando para inspecionar os dados cifrados |

---

## 🛣️ Escolha o seu Caminho de Execução

```
+-------------------------------------------------------------------------------------------------+
|                               QUAL CENÁRIO ATENDE SEU OBJETIVO HOJE?                            |
+--------------------------+------------------------------+---------------------------------------+
| Caminho                  | Banco de Dados               | Melhor caso de uso                    |
+--------------------------+------------------------------+---------------------------------------+
| Caminho 1: Local Rápido  | SQLite Local (arquivo .db)   | Testar a API em 2 minutos sem Docker. |
| Caminho 2: Híbrido       | PostgreSQL (Docker)          | Desenvolvimento ágil com hot-reload.  |
| Caminho 3: Total Docker  | PostgreSQL + API (Docker)    | Demonstração idêntica à produção.     |
| Caminho 4: Scripts Auto  | Automatizado via `scripts/`  | Para agentes de IA e pipelines CI.    |
+--------------------------+------------------------------+---------------------------------------+
```

---

## 🚀 Caminho 1: Execução Local Rápida com SQLite (Zero Docker)

O MedVault vem pré-configurado por padrão para usar **SQLite assíncrono (`aiosqlite`)** caso nenhuma `DATABASE_URL` do Postgres seja fornecida. Esse é o caminho mais leve para estudar o código e a criptografia.

### Passo 1: Criar o Ambiente Virtual e Ativar
Na raiz do projeto:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Passo 2: Atualizar o pip e Instalar Dependências
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### Passo 3: Configurar o Arquivo `.env` (Opcional no SQLite)
Por padrão, se o arquivo `.env` não existir, a aplicação já inicializa em modo seguro com SQLite apontando para `./medvault_demo.db`. Se desejar personalizar:
```bash
cp .env.example .env
```
*(Edite `.env` e deixe `DATABASE_URL="sqlite+aiosqlite:///./medvault_demo.db"`)*.

### Passo 4: Iniciar o Servidor FastAPI
O MedVault cria automaticamente as tabelas SQLite na inicialização via lifecycle assíncrono (`lifespan`):
```bash
export PYTHONPATH="src"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Pronto! A API estará disponível em:
* **Swagger UI Interativo**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Healthcheck**: `curl http://127.0.0.1:8000/api/v1/health`

---

## 🐘 Caminho 2: Híbrido (PostgreSQL no Docker + API Local com Hot-Reload)

Ideal para desenvolvimento diário: o banco de dados roda em um container PostgreSQL 16 isolado com persistência, e a API roda na sua máquina host com recarregamento instantâneo a cada alteração de código.

### Passo 1: Subir Apenas o Banco PostgreSQL
Execute a partir da raiz:
```bash
docker compose up -d db
```
Aguarde alguns segundos até o healthcheck do PostgreSQL ficar saudável:
```bash
docker compose ps
```

### Passo 2: Configurar o `.env`
Copie o modelo de ambiente:
```bash
cp .env.example .env
```
O `.env.example` já está pré-configurado com a URL local do PostgreSQL:
```ini
DATABASE_URL="postgresql+asyncpg://medvault:medvault_secret@localhost:5432/medvault_db"
```

### Passo 3: Aplicar as Migrações Alembic no PostgreSQL
Com a `.venv` ativada:
```bash
source .venv/bin/activate
export PYTHONPATH="src"
alembic upgrade head
```

### Passo 4: Iniciar a API Local
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🐳 Caminho 3: Totalmente Containerizado com Docker Compose

Sobe a API e o PostgreSQL em uma rede interna isolada, rodando com usuário sem privilégios root (`appuser:10001`), healthchecks e migrações automáticas.

### Passo 1: Construir as Imagens e Subir os Serviços
```bash
docker compose up -d --build
```

### Passo 2: Acompanhar os Logs de Inicialização
```bash
docker compose logs -f api
```
Você verá o Alembic executando as migrações (`Running migrations online...`) e em seguida o `uvicorn` inicializando na porta 8000.

### Passo 3: Encerrar os Serviços
```bash
# Para parar sem apagar os dados do banco
docker compose down

# Para parar e resetar completamente o banco de dados (apagando o volume)
docker compose down -v
```

---

## ⚙️ Dicionário de Variáveis de Ambiente (`.env`)

Todas as configurações seguem os princípios da metodologia **12-Factor App** e são validadas em tempo de inicialização pelo Pydantic:

| Variável | Padrão no Código | Descrição Técnica | Nível de Sensibilidade |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `"MedVault Crypto API"` | Nome exibido na documentação Swagger | Baixa |
| `APP_ENV` | `"development"` | Ambiente (`development`, `staging`, `production`) | Baixa |
| `APP_DEBUG` | `true` | Ativa detalhes de log | Baixa |
| `APP_PORT` | `8000` | Porta TCP do servidor web | Baixa |
| `DATABASE_URL` | `sqlite+aiosqlite:///./medvault_demo.db` | String de conexão SQLAlchemy 2.0 Async | **Alta** (Credencial DB) |
| `APP_ENCRYPTION_PEPPER` | *demo-master-encryption-...* | Segredo do servidor para o **HKDF-SHA256**. Deriva as chaves AES-256-GCM por usuário. | **CRÍTICA** (Nunca salvar no DB) |
| `APP_PASSWORD_PEPPER` | *demo-password-secret-...* | Segredo do servidor aplicado via **HMAC-SHA256** antes do hash Argon2id de senhas. | **CRÍTICA** (Nunca salvar no DB) |
| `APP_BLIND_INDEX_PEPPER` | *demo-blind-index-...* | Segredo do servidor para o HMAC dos **Blind Indexes** (Busca exata de CPF/E-mail/Sangue). | **CRÍTICA** (Nunca salvar no DB) |
| `JWT_SECRET_KEY` | *demo-jwt-secret-key-...* | Chave simétrica para assinatura dos Bearer Tokens JWT (HS256). | **CRÍTICA** |

### 🔐 Como Gerar Peppers Criptográficos Fortes para Produção

Nunca use as chaves de demonstração em produção! Para gerar um Pepper com alta entropia criptográfica (mínimo de 32 a 48 bytes aleatórios):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 🕵️ Inspecionando o Banco de Dados Diretamente

Para comprovar que os dados estão realmente criptografados e que dados idênticos geram textos cifrados 100% diferentes, conecte-se diretamente ao banco de dados:

### Cenário A: PostgreSQL (Docker)
```bash
# Acesso interativo via container (não exige cliente psql instalado na máquina host)
docker exec -it medvault-postgres psql -U medvault -d medvault_db
```
Ou se tiver o utilitário `psql` na sua máquina:
```bash
psql "postgresql://medvault:medvault_secret@localhost:5432/medvault_db"
```

### Cenário B: SQLite Local
```bash
sqlite3 medvault_demo.db
```

### Consultas SQL Reveladoras para Testar na Prática:

1. **Verificar os dados pessoais (PII) cifrados e os Blind Indexes na tabela `users`**:
```sql
SELECT 
    id, 
    user_salt, 
    cpf_blind_index, 
    cpf_encrypted, 
    email_blind_index,
    password_hash 
FROM users;
```
*Observe que `cpf_encrypted` começa com `v1$...` contendo o nonce aleatório e o texto cifrado, e `password_hash` está no formato PHC do Argon2id.*

2. **Verificar que prontuários médicos idênticos (`80.0 kg`) geram cifras completamente distintas**:
```sql
SELECT 
    user_id, 
    weight_kg_encrypted, 
    blood_type_blind_index, 
    allergies_encrypted 
FROM medical_records;
```

---

## 🧪 Qualidade de Código, Testes e Linting Manual

Com a `.venv` ativada:

### 1. Executar a Suíte Completa de Testes com Cobertura
Os testes utilizam SQLite assíncrono em memória, sem depender de Docker ou conexões de rede externas:
```bash
pytest -v --cov=src/app --cov-report=term-missing
```

### 2. Verificar Linting e Formatação (Ruff)
```bash
ruff check src tests scripts
ruff format --check src tests scripts
```

### 3. Aplicar Auto-Correção e Formatação
```bash
ruff check --fix src tests scripts
ruff format src tests scripts
```

---

## 🛠️ Solução de Problemas Comuns (Troubleshooting)

1. **Erro: `Address already in use` (Porta 5432 ou 8000 ocupada)**:
   * Verifique se você já possui um PostgreSQL rodando localmente na porta 5432:
     ```bash
     sudo lsof -i :5432
     ```
   * Caso prefira rodar o PostgreSQL do Docker em outra porta, edite o `.env`:
     ```ini
     POSTGRES_PORT=5433
     DATABASE_URL="postgresql+asyncpg://medvault:medvault_secret@localhost:5433/medvault_db"
     ```

2. **Erro: `ModuleNotFoundError: No module named 'app'`**:
   * Certifique-se de definir a variável de ambiente `PYTHONPATH="src"` antes de executar `uvicorn` ou `alembic`:
     ```bash
     export PYTHONPATH="src"
     ```

3. **Resetar completamente o banco de dados**:
   * No SQLite: basta apagar o arquivo local `rm medvault_demo.db`.
   * No PostgreSQL (Docker): `docker compose down -v && docker compose up -d db`.

<div align="center">

# 🔐 MedVault Crypto API

**API de Referência e Estudo para Criptografia de Dados Sensíveis (PII & Prontuários Médicos) no Banco de Dados**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![AEAD: AES-256-GCM](https://img.shields.io/badge/AEAD-AES--256--GCM%20%2B%20HKDF-2E7D32?logo=letsencrypt&logoColor=white)](https://cryptography.io/)
[![Password: Argon2id](https://img.shields.io/badge/Password-Argon2id%20%2B%20Pepper-6A1B9A)](https://argon2-cffi.readthedocs.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?logo=docker&logoColor=white)](./docker-compose.yml)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> [!NOTE]
> ⚠️ **PROJETO DE ESTUDO E REFERÊNCIA ARQUITETURAL DIDÁTICA**
> 
> Este projeto foi desenvolvido com rigor técnico para demonstrar como resolver o desafio de armazenar dados pessoais (**PII**) e prontuários médicos sensíveis (**PHI** sob **LGPD / CFM / HIPAA**) criptografados em repouso no banco de dados, mantendo isolamento por usuário, capacidade de descriptografia pela API e buscas em $O(1)$ via Blind Index.
> 
> *Para ambientes de produção corporativa, os segredos (`Peppers`) devem ser obrigatoriamente integrados a um Hardware Security Module (HSM) ou Key Management Service (AWS KMS, HashiCorp Vault, GCP Cloud KMS).*

---

### 📚 Mapa Completo da Documentação e Apresentações

| Documento | Objetivo |
| :--- | :--- |
| 🛠️ [**Como Executar (Guia Manual Completo)**](./docs/como-executar.md) | Passo a passo manual sem scripts: SQLite local, PostgreSQL no Docker, `.env`, inspeção SQL direta e troubleshooting. |
| 📖 [**Guia Didático de Criptografia**](./docs/guia-didatico-criptografia.md) | Do zero ao avançado: O que é criptografia vs hash vs codificação, Salt, Pepper, Nonce, HKDF, AES-256-GCM, AAD e Blind Index. |
| 🏛️ [**Arquitetura e Engenharia de Software**](./docs/arquitetura-engenharia-software.md) | Como o MedVault implementa Clean Architecture, Clean Code, SOLID, DRY, KISS e Orientação a Objetos no código real. |
| ⚖️ [**Conformidade Regulatória**](./docs/conformidade-regulatoria.md) | Mapeamento das normas médicas e de privacidade: LGPD (Art. 46), CFM 1.821 (NGS2), SBIS, HIPAA e NIST. |
| 📊 [**Catálogo de Diagramas C4 e UML**](./docs/diagramas/) | Diagramas desacoplados em Mermaid (C4 Contexto, Container, Componentes e Sequência de Criptografia). |
| 🖥️ [**Apresentações em Slidev**](./docs/slides/) | 2 decks de slides modernos e interativos para palestras, aulas e demonstrações técnicas. |
| 🤖 [**Guia para Agentes de IA (AGENTS.md)**](./AGENTS.md) | Catálogo de scripts e convenções operacionais para automações e LLMs. |

</div>

---

## ⚡ Quickstart Manual (Coloque a API de pé em 4 comandos!)

Você não precisa de Docker nem de configurações complexas para testar o MedVault. Por padrão, a aplicação roda em **SQLite assíncrono em arquivo local**:

```bash
# 1. Crie o ambiente virtual Python e ative
python3 -m venv .venv
source .venv/bin/activate

# 2. Instale as dependências da aplicação
pip install --upgrade pip
pip install -e ".[dev]"

# 3. Inicie o servidor FastAPI
export PYTHONPATH="src"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Acesse imediatamente a interface interativa:
👉 **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

*(Para rodar com PostgreSQL, Docker Compose completo ou entender as variáveis `.env`, consulte o [Guia Como Executar](./docs/como-executar.md)).*

---

## 🎯 O Dilema Central: "Hash + Salt + Pepper" vs Criptografia de Dados

Uma dúvida extremamente comum entre desenvolvedores e arquitetos é: *"Posso usar **Hash + Salt + Pepper** para proteger o peso do paciente (`80.0 kg`) ou o diagnóstico médico no banco?"*

A resposta técnica é **NÃO** para dados que precisam ser lidos de volta! Cada categoria de dado exige uma ferramenta matemática diferente:

```
+----------------------------------------------------------------------------------------------------+
|                                    A TRÍADE DE SEGURANÇA DO MEDVAULT                               |
+--------------------------+-----------------------+--------------------+----------------------------+
| Categoria de Dado        | Primitiva Utilizada   | É Reversível?      | Onde é aplicado no Projeto |
+--------------------------+-----------------------+--------------------+----------------------------+
| 1. Dados Clínicos & PII  | HKDF-SHA256           | ✅ SIM             | Peso, Altura, Diagnósticos,|
|    (Precisam ser lidos)  | + AES-256-GCM + AAD   | (Reversível com a  | Alergias, Nome, CPF,       |
|                          | com Nonce 96-bit      | chave DEK correta) | E-mail no banco.           |
+--------------------------+-----------------------+--------------------+----------------------------+
| 2. Buscas por Igualdade  | HMAC-SHA256           | ❌ NÃO             | Colunas `*_blind_index`    |
|    (Busca exata O(1))    | com Pepper de Busca   | (Determinístico)   | para CPF, E-mail e Sangue. |
+--------------------------+-----------------------+--------------------+----------------------------+
| 3. Senhas de Acesso      | Argon2id + Salt 16B   | ❌ NÃO             | Coluna `users.password_hash`|
|    (Apenas validação)    | + Pepper do Servidor  | (Irreversível)     | no login (/auth/login).    |
+--------------------------+-----------------------+--------------------+----------------------------+
```

---

## 🔬 A Prova Real: O que fica salvo no banco para `weight_kg = 80.0`?

Quando dois pacientes (**Alice** e **Bruno**) cadastram exatamente o mesmo peso (**`80.0 kg`**), a visão do banco de dados expõe cifras 100% diferentes:

| Paciente | Valor Real (API) | Chave Derivada (HKDF Fingerprint) | Valor Bruto Armazenado na Coluna `weight_kg_encrypted` |
| :--- | :---: | :---: | :--- |
| **Alice** | `80.0` | `sha256:4a9c18f0...3d12e8a1` | `v1$r8mK9pL2xQ1vZ0wN$7fG3kP9mW2xL8qR4tY6uI1oP3aS5dF7gH9jK...` |
| **Bruno** | `80.0` | `sha256:9b2e77c4...8f01a4c9` | `v1$bN4mV6cX8zL0kJ2h$1qW3eR5tY7uI9oP0aS2dF4gH6jK8lZ9xC1vB...` |

> [!IMPORTANT]
> **Imunidade contra Transplante de Dados (AAD)**: Se um invasor copiar o texto cifrado do peso da Alice e colar na coluna de peso do Bruno (ou na coluna de altura da própria Alice), a descriptografia falha na hora com `CryptoIntegrityError (InvalidTag)`, pois os metadados autenticados (`AAD = user:<id>|field:<name>`) não conferem com o contexto da linha/coluna!

---

## 🧪 Testes Automatizados e Qualidade de Código

Para rodar todos os testes unitários e de integração com cobertura:
```bash
pytest -v --cov=src/app --cov-report=term-missing
```

Para verificar estilo e formatação com o Ruff:
```bash
ruff check src tests scripts
ruff format --check src tests scripts
```

---

## 📄 Licença
Distribuído sob a licença **MIT**. Veja [`LICENSE`](./LICENSE) para mais detalhes.

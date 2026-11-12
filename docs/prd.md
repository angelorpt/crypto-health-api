# PRD — Product Requirements Document: MedVault Crypto API

| Metadado | Valor |
| :--- | :--- |
| **Produto** | MedVault Crypto API (Backend Demo) |
| **Versão** | `0.1.0` |
| **Status** | Implementado & Verificado |
| **Stack** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL 16 / SQLite Async, Cryptography, Argon2-CFFI |
| **Licença** | MIT |

---

## 1. Visão Geral e Objetivo

Construir um backend de referência em Python/FastAPI que demonstre, com rigor técnico e boas práticas de engenharia de software (**SOLID, DRY, KISS**), como armazenar dados pessoais (**PII**) e prontuários médicos (**PHI**) criptografados no banco de dados, garantindo que:
1. **Dados idênticos de usuários diferentes** (ex: dois pacientes com peso `80.0 kg`, altura `1.75 m`, tipo sanguíneo `O+`) gerem **textos cifrados completamente distintos** no banco de dados.
2. **A API consiga descriptografar** os dados de forma transparente quando autorizada.
3. **Buscas exatas** por campos sensíveis (CPF, E-mail, Tipo Sanguíneo) continuem rápidas (**O(1)**) sem precisar descriptografar o banco inteiro.
4. **Adulterações ou transplantes de textos cifrados** entre registros ou colunas sejam detectados e bloqueados criptograficamente.

---

## 2. Personas

1. **Arquiteto / Desenvolvedor Avaliador**: Deseja inspecionar o código, rodar os testes automatizados e verificar no Swagger/banco como `HKDF`, `AES-256-GCM`, `AAD`, `Blind Index` e `Argon2id` trabalham juntos.
2. **Aplicação Front-end (Futuro Submodule)**: Consumirá os endpoints REST de CRUD e os endpoints de auditoria `/api/v1/demo/*` para exibir comparativos visuais entre a visão do Banco de Dados (texto cifrado) e a visão da API (texto plano).
3. **Agente de IA / LLM**: Utilizará o `AGENTS.md` e os scripts em `scripts/` para operar, testar, auditar e evoluir o projeto autonomamente.

---

## 3. Requisitos Funcionais (RF)

| ID | Requisito | Critério de Aceite |
| :--- | :--- | :--- |
| **RF-01** | Cadastro de Usuário com PII Criptografada | Ao criar um usuário (`POST /api/v1/users`), `full_name`, `email` e `cpf` devem ser criptografados com `AES-256-GCM` usando chave derivada de `user_salt` + `APP_ENCRYPTION_PEPPER`. |
| **RF-02** | Isolamento Criptográfico por Usuário | Dois usuários com dados médicos idênticos (`weight_kg=80.0`, `height_m=1.75`, `blood_type="O+"`) devem possuir `user_salt`, chaves derivadas, `nonce` e `ciphertext` distintos no banco. |
| **RF-03** | Busca Cega (Blind Index) | Deve ser possível buscar usuários por CPF (`/users/search/by-cpf`), por e-mail (`/users/search/by-email`) e prontuários por tipo sanguíneo (`/medical-records/search/by-blood-type`) via `HMAC-SHA256` indexado. |
| **RF-04** | Hash de Senha com Argon2id + Pepper | Senhas devem passar por `HMAC-SHA256(password, APP_PASSWORD_PEPPER)` antes do hash `Argon2id` com salt aleatório de 16 bytes. |
| **RF-05** | Gestão de Prontuário Médico | Suportar criação/substituição (`PUT /medical-records/user/{id}`), atualização parcial (`PATCH /medical-records/user/{id}`) e leitura descriptografada com cálculo dinâmico de IMC (`bmi`). |
| **RF-06** | Endpoints de Demonstração e Auditoria | Disponibilizar `/demo/seed-comparison`, `/demo/inspect-user/{id}`, `/demo/tamper-check` e `/demo/crypto-playground`. |
| **RF-07** | Autenticação JWT e Verificação Didática | Disponibilizar `/auth/login`, `/auth/me` e `/auth/verify-password`. |

---

## 4. Requisitos Não-Funcionais (RNF)

- **RNF-01 (Segurança AEAD + AAD)**: Todo campo criptografado deve vincular `user:{user_id}|field:{field_name}` no parâmetro *Associated Authenticated Data (AAD)* do `AES-256-GCM`, impedindo ataques de troca de coluna ou de linha.
- **RNF-02 (Separação de Segredos)**: Os *Peppers* (`APP_ENCRYPTION_PEPPER`, `APP_PASSWORD_PEPPER`, `APP_BLIND_INDEX_PEPPER`) jamais devem ser persistidos no banco de dados.
- **RNF-03 (Qualidade & Testes)**: Cobertura de testes unitários e de integração automatizados via `pytest` + linting estrito via `ruff`.
- **RNF-04 (Containerização)**: `Dockerfile` multi-stage executando com usuário não-root e `docker-compose.yml` orquestrando PostgreSQL 16 com healthcheck e migrações Alembic automáticas.

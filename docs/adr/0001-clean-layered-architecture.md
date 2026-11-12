# ADR 0001: Clean Layered Architecture com FastAPI e SQLAlchemy 2.0 Assíncrono

* **Status**: Aceito
* **Data**: 2026-11-11

## Contexto

Este repositório contém o backend Python da demonstração de criptografia em banco de dados e, futuramente, será integrado como um *git submodule* em um repositório *umbrella* ao lado de um repositório Front-end dedicado. Precisamos de uma arquitetura que respeite **SOLID, DRY e KISS**, mantendo a lógica criptográfica totalmente desacoplada do protocolo HTTP (FastAPI) e do mecanismo de persistência (SQLAlchemy).

## Decisão

Adotamos uma **Clean Layered Architecture enxuta** organizada em `src/app/`:

1. **`core/`**: Configurações (`config.py`), motor criptográfico puro sem dependência de banco ou HTTP (`crypto.py`), utilitários JWT (`security.py`) e sessão assíncrona do banco (`database.py`).
2. **`models/`**: Entidades ORM do SQLAlchemy 2.0 (`User`, `MedicalRecord`) refletindo fielmente as colunas físicas do banco (`*_encrypted`, `*_blind_index`, `user_salt`, `password_hash`).
3. **`schemas/`**: Contratos de entrada e saída validados com Pydantic v2.
4. **`repositories/`**: Camada de acesso a dados (`UserRepository`, `MedicalRecordRepository`) encapsulando queries SQLAlchemy.
5. **`services/`**: Orquestração de regras de negócio e criptografia/descriptografia (`UserService`, `MedicalRecordService`, `DemoService`).
6. **`api/v1/`**: Routers FastAPI enxutos que apenas recebem requisições HTTP, delegam aos serviços injetados via `deps.py` e retornam os schemas Pydantic.

## Consequências

* **Positivas**:
  * O motor criptográfico (`app.core.crypto`) pode ser testado unitariamente em milissegundos sem subir banco de dados ou servidor HTTP.
  * Visibilidade explícita da diferença entre o modelo físico persistido (`models/medical_record.py` com `weight_kg_encrypted: str`) e o modelo de domínio/API (`schemas/medical_record.py` com `weight_kg: float`).
* **Negativas / Trade-offs**:
  * Como a criptografia usa o `user_salt` e o `user_id` do usuário dono do registro (HKDF + AAD), a transformação ocorre de forma explícita na camada `Service` em vez de uma coluna mágica global do ORM — o que na prática aumenta a clareza e evita consultas implícitas ocultas.

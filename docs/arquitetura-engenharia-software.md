# Arquitetura e Engenharia de Software no MedVault Crypto API

> **Mapeamento prático de Clean Architecture, Clean Code, Princípios SOLID, DRY, KISS e Orientação a Objetos no código real da aplicação.**

Este documento serve como referência de engenharia de software para explicar como padrões de arquitetura e boas práticas de código foram aplicados no backend em Python (`FastAPI` + `SQLAlchemy 2.0 Async`).

---

## 🏛️ 1. Clean Architecture (Arquitetura em Camadas)

A arquitetura do MedVault segue o princípio fundamental da Clean Architecture: **as dependências apontam para dentro**. Módulos de regras de negócio puras (criptografia e domínios) não dependem de frameworks web ou de drivers de banco de dados.

```
+----------------------------------------------------------------------------------------------------+
|                                    CAMADAS DA CLEAN ARCHITECTURE                                   |
+--------------------------+------------------------------------+------------------------------------+
| Camada                   | Diretório no Projeto               | Responsabilidade Única             |
+--------------------------+------------------------------------+------------------------------------+
| 1. Core (Entidades Puras)| `src/app/core/crypto.py`           | Primitivas matemáticas puras:      |
|    e Domínio Criptográfico|                                   | HKDF, AES-GCM, HMAC, Argon2id.     |
|                          |                                    | Zero dependência do FastAPI/DB.    |
+--------------------------+------------------------------------+------------------------------------+
| 2. Modelos & Contratos   | `src/app/models/`                  | Modelos ORM do SQLAlchemy 2.0.     |
|    (Data / Domain)       | `src/app/schemas/`                 | Contratos Pydantic v2 validados.   |
+--------------------------+------------------------------------+------------------------------------+
| 3. Repositories          | `src/app/repositories/`            | Isolamento de acesso a dados SQL.  |
|    (Persistência)        |                                    | Executa queries com AsyncSession.  |
+--------------------------+------------------------------------+------------------------------------+
| 4. Services              | `src/app/services/`                | Orquestração de negócio e cripto.  |
|    (Regras de Negócio)   |                                    | Junta Repositórios + Criptografia. |
+--------------------------+------------------------------------+------------------------------------+
| 5. Adapters HTTP         | `src/app/api/v1/`                  | Routers FastAPI, endpoints REST e  |
|    (Interface Externa)   | `src/app/api/deps.py`              | injeção de dependências.           |
+--------------------------+------------------------------------+------------------------------------+
```

---

## 🧩 2. Princípios SOLID Aplicados no Código

### 1. SRP — Single Responsibility Principle (Princípio da Responsabilidade Única)
*Uma classe ou módulo deve ter um, e apenas um, motivo para mudar.*

* **No Código**: Em vez de criar uma classe genérica gigantesca de segurança (`SecurityManager`), o arquivo `crypto.py` divide as operações em 3 classes especializadas:
  1. `PasswordCryptoService`: Cuida exclusivamente de hash e verificação de senhas com Argon2id.
  2. `BlindIndexService`: Cuida exclusivamente de normalização de termos e cálculo determinístico de HMAC-SHA256 para busca.
  3. `FieldEncryptionService`: Cuida exclusivamente de derivação de chave por usuário (HKDF), empacotamento do envelope `v1$` e cifragem/decifragem com AES-256-GCM + AAD.

### 2. OCP — Open/Closed Principle (Princípio Aberto/Fechado)
*Entidades de software devem estar abertas para extensão, mas fechadas para modificação.*

* **No Código**: O envelope de armazenamento criptográfico utiliza versionamento explícito:
  ```text
  v1$<nonce_base64>$<ciphertext_tag_base64>
  ```
  Caso a organização decida no futuro migrar do `AES-256-GCM` para algoritmos pós-quânticos (como Kyber/Dilithium) ou `ChaCha20-Poly1305`, podemos criar o envelope `v2$...` sem quebrar nenhum dos registros `v1$` gravados anteriormente no banco.

### 3. LSP — Liskov Substitution Principle (Princípio da Substituição de Liskov)
*Subclasses devem poder substituir suas classes base sem quebrar o comportamento do sistema.*

* **No Código**: O `database.py` expõe a classe declarativa `Base(DeclarativeBase)` do SQLAlchemy 2.0. Os modelos `User` e `MedicalRecord` estendem essa base mantendo a mesma semântica de mapeamento relacional assíncrono.

### 4. ISP — Interface Segregation Principle (Princípio da Segregação de Interfaces)
*Clientes não devem ser forçados a depender de métodos que não utilizam.*

* **No Código**: Os repositórios (`UserRepository` e `MedicalRecordRepository`) e os schemas Pydantic segregam interfaces de leitura e escrita:
  * `UserCreate`: Exige a senha pura para realizar o hash.
  * `UserResponse`: Omite intencionalmente a senha e o hash, expondo apenas dados descriptografados autorizados.

### 5. DIP — Dependency Inversion Principle (Princípio da Inversão de Dependência)
*Módulos de alto nível não devem depender de módulos de baixo nível; ambos devem depender de abstrações.*

* **No Código**: Os controladores HTTP (`routers`) nunca instanciam diretamente conexões de banco ou chaves secretas. Eles recebem os serviços por injeção de dependência via `Depends()` em `src/app/api/deps.py`:
  ```python
  @router.post("/users", response_model=UserResponse)
  async def create_user(
      payload: UserCreate,
      user_service: UserService = Depends(get_user_service),
  ):
      return await user_service.create_user(payload)
  ```

---

## 🎨 3. Design Patterns Adotados

### 1. Facade Pattern (Padrão Fachada)
* Fornece uma interface simplificada para um subsistema complexo.
* **No Código**: A dataclass `CryptoSuite` e a função de fábrica `build_crypto_suite()` em `crypto.py`:
  ```python
  @dataclass(frozen=True)
  class CryptoSuite:
      passwords: PasswordCryptoService
      blind_index: BlindIndexService
      fields: FieldEncryptionService
  ```
  Permite que qualquer serviço acesse os três subsistemas criptográficos através de uma única instância unificada.

### 2. Application Factory Pattern
* Centraliza a criação e configuração da aplicação web.
* **No Código**: A função `create_app()` em `main.py` instancia a aplicação FastAPI, configura middlewares de CORS, registra rotas e handlers de lifecycle, facilitando testes automatizados isolados.

---

## 🎯 4. Boas Práticas: DRY, KISS e Clean Code

### DRY (Don't Repeat Yourself)
* O processo de codificação/decodificação em Base64 URL-safe com tratamento de padding é centralizado nas funções auxiliares `_b64url_encode` e `_b64url_decode`.
* A regra de normalização para busca cega (remover pontuação de CPF, converter e-mail para minúsculo) fica isolada em `BlindIndexService.normalize()`.

### KISS (Keep It Simple, Stupid)
* **Zero Overengineering**: Não foram introduzidos microserviços ou mensagerias desnecessárias para um problema de criptografia em repouso.
* **SQLite por Padrão**: Permite que qualquer desenvolvedor clone o repositório e rode a API imediatamente sem precisar configurar um servidor PostgreSQL local.

### Clean Code e Convenções
* **Tipagem Estrita**: Suporte completo a Type Hints do Python 3.11+ (`dataclass(frozen=True)`, tipos genéricos assíncronos `AsyncGenerator`).
* **Convenção de Idioma**:
  * Código-fonte, nomes de colunas, variáveis e rotas REST em **Inglês** (`weight_kg_encrypted`, `/api/v1/medical-records`).
  * Documentação, docstrings e mensagens de erro do Swagger em **Português (PT-BR)**.
* **Imutabilidade e Segurança**: Uso de estruturas imutáveis (`frozen=True`) para inspeções de tokens criptográficos (`CiphertextInspection`).

# Diagrama C4: Nível 3 — Componentes

> **Decomposição interna do container `medvault-api` mostrando Clean Architecture e Clean Code.**

Este diagrama detalha a estrutura interna de componentes dentro do backend seguindo o modelo C4 (Nível 3).

```mermaid
flowchart TB
    subgraph HTTP["Camada 5: Adapters HTTP (api/v1)"]
        UserRouter["UserRouter<br/>[api/v1/endpoints/users.py]"]
        MedRouter["MedicalRecordRouter<br/>[api/v1/endpoints/medical_records.py]"]
        AuthRouter["AuthRouter<br/>[api/v1/endpoints/auth.py]"]
        DemoRouter["DemoRouter<br/>[api/v1/endpoints/demo.py]"]
        Deps["Dependency Injection<br/>[api/deps.py]"]
    end

    subgraph Services["Camada 4: Services (services/)"]
        UserService["UserService<br/>Orquestra criação, login e busca"]
        MedService["MedicalRecordService<br/>Orquestra prontuários e IMC"]
        DemoService["DemoService<br/>Comparações lado a lado e tamper checks"]
    end

    subgraph Repositories["Camada 3: Repositories (repositories/)"]
        UserRepo["UserRepository<br/>Consultas SQL na tabela users"]
        MedRepo["MedicalRecordRepository<br/>Consultas SQL na tabela medical_records"]
    end

    subgraph CoreCrypto["Camada 1: Core Cripto Puro (core/crypto.py)"]
        CryptoSuite["CryptoSuite (Facade)"]
        FieldEnc["FieldEncryptionService<br/>HKDF-SHA256 + AES-256-GCM + AAD"]
        BlindIdx["BlindIndexService<br/>HMAC-SHA256(pepper, field:val)"]
        PwdCrypto["PasswordCryptoService<br/>HMAC-SHA256 + Argon2id"]
    end

    subgraph ModelsSchemas["Camadas de Domínio & Contratos"]
        Schemas["Pydantic Schemas<br/>[schemas/*.py]"]
        ORMModels["SQLAlchemy Models<br/>[models/*.py]"]
    end

    HTTP -->|Injeta dependências| Deps
    Deps --> Services
    Services --> Repositories
    Services --> CryptoSuite
    CryptoSuite --> FieldEnc & BlindIdx & PwdCrypto

    Repositories --> ORMModels
    Services --> Schemas
    HTTP --> Schemas

    classDef http fill:#1E88E5,stroke:#0D47A1,stroke-width:2px,color:#fff;
    classDef srv fill:#43A047,stroke:#1B5E20,stroke-width:2px,color:#fff;
    classDef repo fill:#00ACC1,stroke:#006064,stroke-width:2px,color:#fff;
    classDef crypto fill:#8E24AA,stroke:#4A148C,stroke-width:2px,color:#fff;
    classDef data fill:#FB8C00,stroke:#E65100,stroke-width:2px,color:#fff;

    class UserRouter,MedRouter,AuthRouter,DemoRouter,Deps http;
    class UserService,MedService,DemoService srv;
    class UserRepo,MedRepo repo;
    class CryptoSuite,FieldEnc,BlindIdx,PwdCrypto crypto;
    class Schemas,ORMModels data;
```

---

### O que este nível explica:
1. **Adapters HTTP**: Recebem requisições REST e validam payloads via Schemas Pydantic.
2. **Services**: Contêm a lógica de negócio e coordenam a criptografia e persistência.
3. **Core Crypto**: Módulo agnóstico e independente que executa o trabalho matemático pesado.
4. **Repositories**: Isolam a linguagem SQL e o ORM do restante da aplicação.

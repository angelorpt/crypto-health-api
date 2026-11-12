# Diagrama C4: Nível 1 — Contexto de Sistema

> **Visão geral de alto nível dos usuários, atores externos e fronteiras do sistema MedVault Crypto API.**

Este diagrama segue o modelo C4 (Nível 1 - Contexto) utilizando a sintaxe nativa e robusta de grafos do Mermaid (`flowchart TB`).

```mermaid
flowchart TB
    subgraph Users["Atores e Clientes Externos"]
        Doctor["👨‍⚕️ Médico / Profissional de Saúde<br/>(Consulta e atualiza prontuários)"]
        Patient["🧑 Paciente / Usuário Comum<br/>(Consulta seu próprio cadastro e histórico)"]
        Attacker["🥷 Atacante / Invasor de Banco<br/>(Tenta roubar dump SQL ou forjar dados)"]
    end

    subgraph Boundary["Fronteira do Sistema MedVault"]
        API["🔐 MedVault Crypto API<br/>[Sistema / FastAPI]<br/>API REST que recebe dados em texto plano e aplica<br/>HKDF + AES-256-GCM + Blind Index + Argon2id"]
    end

    subgraph Storage["Armazenamento & Segredos Externos"]
        DB[("🗄️ Banco de Dados<br/>[PostgreSQL 16 / SQLite]<br/>Armazena apenas Ciphertexts com Nonce,<br/>Blind Indexes HMAC e Hashes Argon2id")]
        KMS["🌶️ Cofre de Segredos<br/>[Ambiente .env / AWS KMS / Vault]<br/>Guarda APP_ENCRYPTION_PEPPER,<br/>APP_BLIND_INDEX_PEPPER e APP_PASSWORD_PEPPER"]
    end

    Doctor -->|1. Envia prontuário em texto plano / Consulta IMC| API
    Patient -->|2. Realiza cadastro e login com senha| API
    API -->|3. Persiste dados cifrados e busca por Blind Index| DB
    API -->|4. Lê Peppers secretos fora do banco| KMS
    Attacker -.->|5. Tenta ler dump roubado ou forjar coluna| DB

    classDef actor fill:#1E88E5,stroke:#0D47A1,stroke-width:2px,color:#fff;
    classDef system fill:#43A047,stroke:#1B5E20,stroke-width:2px,color:#fff;
    classDef storage fill:#FB8C00,stroke:#E65100,stroke-width:2px,color:#fff;
    classDef attacker fill:#E53935,stroke:#B71C1C,stroke-width:2px,color:#fff;

    class Doctor,Patient actor;
    class API system;
    class DB,KMS storage;
    class Attacker attacker;
```

---

### O que este nível explica:
1. **O Médico e o Paciente** interagem com a API fornecendo dados normais em texto plano (`80.0 kg`, `O+`, `Dipirona`).
2. **A API MedVault** atua como o guardião criptográfico: transforma o dado antes de salvar e descriptografa ao responder.
3. **O Banco de Dados** nunca enxerga o dado original. Mesmo que o **Invasor** obtenha acesso irrestrito ao banco de dados, ele só encontra ruído aleatório incompreensível, pois os **Peppers** estão salvos exclusivamente no cofre do servidor.

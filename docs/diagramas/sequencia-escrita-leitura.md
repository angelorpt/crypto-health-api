# Diagrama de Sequência: Ciclo de Vida da Criptografia (Escrita e Leitura)

> **Fluxo passo a passo demonstrando a cifragem com HKDF + AES-256-GCM + AAD na gravação e a validação de integridade na leitura.**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as 📱 Cliente / Médico
    participant API as ⚡ FastAPI Router
    participant Srv as ⚙️ MedicalRecordService
    participant Crypto as 🔐 FieldEncryptionService
    participant HKDF as 🔑 HKDF-SHA256
    participant AES as 🛡️ AES-256-GCM
    participant DB as 🗄️ PostgreSQL / SQLite

    Note over Cliente,DB: FLUXO DE ESCRITA: Gravação de Prontuário (weight_kg = 80.0)

    Cliente->>API: PUT /api/v1/medical-records/user/{user_id}<br/>Payload: { weight_kg: 80.0, blood_type: "O+" }
    API->>Srv: update_record(user_id, payload)
    Srv->>DB: Busca user_salt do paciente
    DB-->>Srv: Retorna user_salt (32 bytes aleatórios)

    Srv->>Crypto: encrypt_float(80.0, user_id, user_salt, "weight_kg")
    Crypto->>HKDF: derive(APP_ENCRYPTION_PEPPER, user_salt)
    HKDF-->>Crypto: Retorna Chave DEK exclusiva do usuário (256 bits)
    
    Crypto->>Crypto: Gera Nonce aleatório de 96 bits (12 bytes)
    Crypto->>Crypto: Constrói AAD = "user:{user_id}|field:weight_kg"
    
    Crypto->>AES: encrypt(key=DEK, nonce=Nonce, plaintext="80.00", aad=AAD)
    AES-->>Crypto: Retorna ciphertext + Auth Tag (16 bytes)
    Crypto-->>Srv: Retorna token empacotado: "v1$<nonce>$<ciphertext+tag>"

    Srv->>DB: INSERT / UPDATE medical_records (weight_kg_encrypted = token)
    DB-->>Srv: Confirmação de gravação
    Srv-->>API: Prontuário gravado com sucesso
    API-->>Cliente: 200 OK (Dados descriptografados e IMC calculado)

    Note over Cliente,DB: FLUXO DE LEITURA: Consulta de Prontuário pelo Médico

    Cliente->>API: GET /api/v1/medical-records/user/{user_id}
    API->>Srv: get_record(user_id)
    Srv->>DB: SELECT weight_kg_encrypted, user_salt FROM medical_records JOIN users
    DB-->>Srv: Retorna "v1$<nonce>$<ciphertext+tag>" e user_salt

    Srv->>Crypto: decrypt_float(token, user_id, user_salt, "weight_kg")
    Crypto->>HKDF: derive(APP_ENCRYPTION_PEPPER, user_salt)
    HKDF-->>Crypto: Retorna a mesma Chave DEK de 256 bits
    
    Crypto->>Crypto: Desempacota Nonce e Ciphertext+Tag
    Crypto->>Crypto: Reconstrói AAD = "user:{user_id}|field:weight_kg"
    
    Crypto->>AES: decrypt(key=DEK, nonce=Nonce, ciphertext=Ciphertext+Tag, aad=AAD)
    
    alt Tag e AAD válidos
        AES-->>Crypto: Retorna plaintext "80.00"
        Crypto-->>Srv: Retorna float 80.0
        Srv-->>API: Monta resposta JSON com IMC (ex: 26.12)
        API-->>Cliente: 200 OK (Texto claro)
    else Dado adulterado no banco ou AAD incorreto (Transplante)
        AES-->>Crypto: InvalidTag Exception!
        Crypto-->>Srv: CryptoIntegrityError
        Srv-->>API: 422 / 403 Erro de integridade criptográfica
        API-->>Cliente: 🚨 Alerta de Adulteração de Dados
    end
```

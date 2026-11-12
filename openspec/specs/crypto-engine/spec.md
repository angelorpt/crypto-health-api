# Especificação: Motor Criptográfico (`crypto-engine`)

## Objetivo

Definir os requisitos formais para criptografia de campos sensíveis por usuário, geração de índices cegos (Blind Indexes) e hash de senhas na aplicação MedVault Crypto API.

## Requisitos

### Requirement: Isolamento Criptográfico por Usuário (HKDF + AES-256-GCM + AAD)
O sistema SHALL criptografar cada campo sensível de usuário e prontuário médico utilizando uma chave simétrica de 256 bits derivada exclusivamente para aquele usuário via `HKDF-SHA256(APP_ENCRYPTION_PEPPER, user_salt)` combinada com o algoritmo `AES-256-GCM`, um `nonce` criptograficamente aleatório de 96 bits por operação e `AAD` contendo `user:{user_id}|field:{field_name}`.

#### Scenario: Dois usuários com o mesmo peso (80.0 kg)
- **WHEN** o Paciente A e o Paciente B cadastram prontuários médicos com `weight_kg = 80.0`
- **THEN** os valores `weight_kg_encrypted` armazenados no banco de dados SHALL ser completamente diferentes entre si, e ambos SHALL ser descriptografados pela API de volta para `80.0`.

#### Scenario: Tentativa de transplante de ciphertext entre usuários ou colunas
- **WHEN** um texto cifrado de `weight_kg_encrypted` do Paciente A é lido no contexto do Paciente B ou na coluna `height_m` do próprio Paciente A
- **THEN** a operação de descriptografia SHALL falhar imediatamente lançando `CryptoIntegrityError` devido à falha na tag de autenticação GCM / AAD.

### Requirement: Busca Exata Cega (HMAC-SHA256 Blind Index)
O sistema SHALL permitir buscas por igualdade em campos selecionados (`email`, `cpf`, `blood_type`) através de um índice determinístico calculado com `HMAC-SHA256(APP_BLIND_INDEX_PEPPER, "{field_name}:{normalized_value}")`.

#### Scenario: Busca de usuário por CPF com ou sem pontuação
- **WHEN** um usuário é cadastrado com CPF `"123.456.789-01"` e uma busca é realizada por `"12345678901"`
- **THEN** o `BlindIndexService` SHALL normalizar ambos para `"12345678901"`, gerar o mesmo hash HMAC-SHA256 e localizar o registro em $O(1)$ sem descriptografar a tabela.

### Requirement: Hash de Senha com Argon2id + Salt + Pepper
O sistema SHALL armazenar senhas utilizando `HMAC-SHA256(APP_PASSWORD_PEPPER, plain_password)` seguido de `Argon2id` com salt aleatório de 16 bytes.

#### Scenario: Dois usuários com a mesma senha
- **WHEN** dois usuários cadastram exatamente a mesma senha `"MesmaSenha@123"`
- **THEN** os valores `password_hash` armazenados no banco SHALL ser distintos e verificáveis apenas na presença do `APP_PASSWORD_PEPPER` correto.

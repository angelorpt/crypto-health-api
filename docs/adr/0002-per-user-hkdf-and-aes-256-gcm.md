# ADR 0002: Criptografia de Campos com HKDF por Usuário (Salt + Pepper) e AES-256-GCM com AAD

* **Status**: Aceito
* **Data**: 2026-11-11

## Contexto

O objetivo central do projeto é garantir que dados médicos e pessoais repetidos entre vários usuários — por exemplo, vários pacientes pesando `80.0 kg` ou com tipo sanguíneo `O+` — fiquem **completamente diferentes no banco de dados**, mas ainda possam ser **lidos e exibidos pela API**.

Surgiu inicialmente a dúvida se **Hash + Salt + Pepper** resolveria esse requisito para todos os campos.

## Decisão

1. **Por que NÃO usar Hash + Salt + Pepper nos campos médicos/PII**:
   * Funções de hash criptográfico (`SHA-256`, `Argon2id`, `bcrypt`) são **unidirecionais (irreversíveis)**. Se salvarmos apenas o hash de `80.0 kg`, a API jamais conseguirá recuperar o número `80.0` para exibir no prontuário ou calcular o IMC. Portanto, **Hash + Salt + Pepper é utilizado exclusivamente para senhas** (ver ADR 0004) e **HMAC + Pepper para Blind Indexes de busca** (ver ADR 0003).
2. **Como aproveitar o conceito de Salt + Pepper na Criptografia Reversível**:
   * Aplicamos o conceito de **Salt por usuário + Pepper do servidor** dentro de uma função de derivação de chave (**KDF**):
     $$\text{DEK}_{\text{user}} = \text{HKDF-SHA256}(\text{IKM} = \text{APP\_ENCRYPTION\_PEPPER}, \text{salt} = \text{user\_salt}, \text{info} = \text{"medvault-aes256gcm-user-dek-v1"})$$
   * Cada usuário recebe um `user_salt` aleatório de 32 bytes salvo no banco, enquanto o `APP_ENCRYPTION_PEPPER` reside exclusivamente nas variáveis de ambiente do servidor.
3. **Criptografia Autenticada com Dados Associados (`AES-256-GCM` + `Nonce` 96 bits + `AAD`)**:
   * Cada campo é criptografado com a chave $\text{DEK}_{\text{user}}$ usando `AES-256-GCM` e um `nonce` criptograficamente aleatório de 12 bytes (`os.urandom(12)`).
   * Passamos `user:{user_id}|field:{field_name}` como **AAD (Associated Authenticated Data)**.
   * O valor salvo no banco segue o formato de envelope versionado:
     `v1$<nonce_base64url>$<ciphertext_and_tag_base64url>`.

## Consequências

* **Dois usuários com `80.0 kg`** possuem chaves derivadas diferentes ($\text{DEK}_A \neq \text{DEK}_B$), nonces diferentes e AADs diferentes: os textos cifrados são 100% distintos.
* **O mesmo usuário salvando `80.0 kg` duas vezes** gera dois textos cifrados distintos (graças ao nonce aleatório de 96 bits).
* **Proteção contra transplante (Tamper-Proof)**: Um invasor com acesso de escrita ao banco não consegue copiar o `weight_kg_encrypted` do Usuário A e colar no Usuário B, nem trocar `weight_kg_encrypted` por `height_m_encrypted` do próprio Usuário A, pois a verificação da tag GCM de 128 bits falhará imediatamente (`InvalidTag`).

---
marp: true
theme: default
paginate: true
header: "MedVault Crypto API — Criptografia de Dados Sensíveis no Banco de Dados"
footer: "FastAPI • SQLAlchemy 2.0 • AES-256-GCM • HKDF • Blind Index (HMAC) • Argon2id"
---

# 🔐 Criptografia de Dados no Banco de Dados na Prática
### Como proteger PII e Prontuários Médicos garantindo que dados iguais (`80.0 kg`) gerem valores 100% diferentes no banco

**Projeto Demo: MedVault Crypto API**
*Python • FastAPI • SQLAlchemy 2.0 • PostgreSQL 16*

<!--
Notas do Apresentador:
- Boas-vindas! Hoje vamos resolver um problema real de engenharia de segurança e privacidade (LGPD / HIPAA).
- Como salvar dados sensíveis de usuários e prontuários médicos no banco de dados de forma que mesmo valores idênticos (como dois pacientes que pesam 80 kg ou têm tipo sanguíneo O+) fiquem completamente diferentes no banco, mas continuem pesquisáveis e legíveis pela API.
-->

---

## 📌Slide 2: O Problema Real

Imagine um banco de dados de saúde com **100.000 pacientes**:
- Muitos pacientes pesam **`80.0 kg`** ou medem **`1.75 m`**.
- ~40% dos pacientes possuem tipo sanguíneo **`O+`**.
- Milhares têm diagnóstico de **`Hipertensão`** ou alergia a **`Dipirona`**.

**O que acontece se salvarmos em texto plano ou com criptografia ingênua?**
1. **Texto Plano**: Qualquer vazamento de backup SQL ou acesso de DBA expõe tudo.
2. **Criptografia Determinística Simples**: Todos os pacientes com `80.0 kg` terão o mesmo texto cifrado `X9f2...` — um invasor descobre padrões por análise de frequência!

---

## 📌 Slide 3: A Dúvida Clássica — "Hash + Salt + Pepper Resolve?"

Muitas vezes surge a sugestão: *"Vamos aplicar **Hash + Salt + Pepper** nos dados!"*

| Pergunta | Hash + Salt + Pepper (`Argon2id`) | Criptografia Simétrica (`AES-256-GCM`) |
| :--- | :---: | :---: |
| **Dados iguais ficam diferentes?** | ✅ Sim | ✅ Sim |
| **Protege contra vazamento do banco?** | ✅ Sim | ✅ Sim |
| **A API consegue ler `80.0 kg` de volta?** | ❌ **NÃO! (Irreversível)** | ✅ **SIM! (Reversível com a chave)** |

> **Conclusão de Arquitetura**:
> - **Senhas** usam **Hash + Salt + Pepper** (`Argon2id`) porque ninguém nunca precisa ler a senha de volta.
> - **Dados Médicos e PII** (`80.0 kg`, `O+`, `CPF`) precisam ser lidos pela API! Então usamos **Salt + Pepper para derivar uma Chave por Usuário (`HKDF`)** + **Criptografia Autenticada (`AES-256-GCM`)**!

---

## 📌 Slide 4: Os 3 Pilares da Nossa Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PILAR 1: CRIPTOGRAFIA DE CAMPOS                      │
│   HKDF-SHA256(EncryptionPepper + user_salt) ──► Chave DEK do Usuário    │
│   AES-256-GCM(DEK, Nonce Aleatório 96-bit, AAD = user_id + field_name)  │
│   ► Usado em: Peso, Altura, Sangue, Alergias, Diagnósticos, CPF, Email  │
├─────────────────────────────────────────────────────────────────────────┤
│                    PILAR 2: BUSCA CEGA (BLIND INDEX)                    │
│   HMAC-SHA256(BlindIndexPepper, "campo:valor_normalizado")              │
│   ► Usado em: Busca exata O(1) por CPF, E-mail e Tipo Sanguíneo         │
├─────────────────────────────────────────────────────────────────────────┤
│                    PILAR 3: HASH DE SENHA IRREVERSÍVEL                  │
│   HMAC-SHA256(PasswordPepper, senha) ──► Argon2id(Salt Aleatório 16B)   │
│   ► Usado em: Autenticação de Usuários (/auth/login)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 Slide 5: Conceito 1 — Salt vs. Pepper

Por que combinamos **Salt** e **Pepper** em vez de usar apenas um deles?

* 🧂 **Salt (Sal — Público por Usuário, salvo no Banco)**:
  * 32 bytes aleatórios na coluna `users.user_salt` (e 16 bytes no `Argon2id`).
  * Garante que **Alice** e **Bruno** nunca compartilhem a mesma chave nem o mesmo hash.
* 🌶️ **Pepper (Pimenta — Secreta do Servidor, salva apenas no `.env` / KMS)**:
  * Fica **fora do banco de dados** (`APP_ENCRYPTION_PEPPER`, `APP_PASSWORD_PEPPER`, `APP_BLIND_INDEX_PEPPER`).
  * Se um invasor roubar o backup inteiro do PostgreSQL, ele tem os *Salts* e os *Ciphertexts*, mas **não tem os Peppers**!

---

## 📌 Slide 6: Conceito 2 — Derivação de Chave por Usuário com `HKDF-SHA256`

Como dar uma chave de criptografia exclusiva de 256 bits para cada usuário sem salvar chaves no banco?

```python
def derive_user_key(self, user_salt: str) -> bytes:
    """Deriva uma chave DEK de 256 bits para o usuário via HKDF-SHA256(Pepper + User Salt)."""
    salt_bytes = _b64url_decode(user_salt)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32, # 256 bits
        salt=salt_bytes,
        info=b"medvault-aes256gcm-user-dek-v1",
    )
    return hkdf.derive(self._pepper_bytes)
```

- **Alice** (`salt_A`) + `ServerPepper` $\rightarrow$ $\text{DEK}_{\text{Alice}}$
- **Bruno** (`salt_B`) + `ServerPepper` $\rightarrow$ $\text{DEK}_{\text{Bruno}}$
- Chaves **100% diferentes** calculadas em memória em microssegundos!

---

## 📌 Slide 7: Conceito 3 — `AES-256-GCM` + `Nonce` de 96 bits

Mesmo tendo chaves diferentes por usuário, e se a **mesma usuária (Alice)** atualizar o peso de `80.0 kg` para `80.0 kg` novamente?

- A cada gravação, sorteamos um **Nonce (Number Used Once)** de 12 bytes (`os.urandom(12)`).
- O valor salvo no banco é empacotado como:
  `v1$<nonce_base64url>$<ciphertext_e_tag_base64url>`
- Resultado:
  - **Alice** (`80.0 kg`) $\neq$ **Bruno** (`80.0 kg`)
  - **Alice 1ª gravação** (`80.0 kg`) $\neq$ **Alice 2ª gravação** (`80.0 kg`)
  - E a API descriptografa todos de volta para `80.0`!

---

## 📌 Slide 8: Conceito 4 — Proteção contra Transplante com `AAD`

**Pergunta de Segurança**: E se um DBA malicioso copiar o texto cifrado de `weight_kg` (`80.0`) da Alice e colar na coluna `height_m` (altura) da própria Alice?

Para impedir isso, usamos o **AAD (Associated Authenticated Data)** do `AES-256-GCM`:

```python
@staticmethod
def build_aad(user_id: str, field_name: str) -> bytes:
    return f"user:{user_id}|field:{field_name}".encode("utf-8")
```

- A Tag de Autenticação de 128 bits do GCM sela matematicamente o texto cifrado com `user:<id>|field:weight_kg`.
- Se alguém tentar ler aquele valor como `height_m` ou em outro `user_id`, o `AES-256-GCM` lança `InvalidTag` imediatamente!

---

## 📌 Slide 9: Conceito 5 — Busca Exata em $O(1)$ com Blind Index (`HMAC-SHA256`)

Se cada criptografia gera um texto diferente, como buscar um paciente por **CPF**, **E-mail** ou **Tipo Sanguíneo (`O+`)** sem descriptografar 100.000 linhas?

```python
def compute_index(self, field_name: str, value: str) -> str:
    normalized = self.normalize(field_name, value)
    domain_input = f"{field_name}:{normalized}".encode("utf-8")
    return hmac.new(self._pepper_bytes, domain_input, hashlib.sha256).hexdigest()
```

1. Na gravação: salvamos `cpf_encrypted` (AES-GCM) + `cpf_blind_index` (HMAC-SHA256).
2. Na busca (`GET /api/v1/users/search/by-cpf?cpf=123.456.789-01`):
   - Normalizamos para `12345678901`.
   - Calculamos o HMAC com o `APP_BLIND_INDEX_PEPPER`.
   - O banco faz `WHERE cpf_blind_index = 'a9f1...'` usando índice B-Tree em **$O(1)$**!

---

## 📌 Slide 10: Conceito 6 — Senhas com `Argon2id` + `Salt` + `Pepper`

Para a senha do usuário, aplicamos defesa em profundidade em 2 camadas:

1. **Camada 1 (Pepper do Servidor)**:
   `peppered = HMAC-SHA256(APP_PASSWORD_PEPPER, plain_password)`
2. **Camada 2 (Argon2id Memory-Hard + Salt de 16 bytes)**:
   `$argon2id$v=19$m=19456,t=2,p=2$<salt_16B>$<hash_32B>`

- **Por que `HMAC-SHA256` antes do `Argon2id`?**
  Porque se o banco de dados vazar, um atacante com milhares de GPUs não pode sequer iniciar um ataque de dicionário sem antes possuir o `APP_PASSWORD_PEPPER` do servidor!

---

## 📌 Slide 11: Demonstração ao Vivo (Live Demo!)

Hora de ver funcionando na prática:

1. **No Terminal**:
   ```bash
   bash scripts/demo-scenario.sh
   ```
2. **No Navegador (Swagger UI — `http://localhost:8000/docs`)**:
   - `POST /api/v1/demo/seed-comparison`: Cria Alice e Bruno com **`80.0 kg`, `1.75 m`, `O+`** e compara os textos cifrados lado a lado.
   - `GET /api/v1/demo/inspect-user/{user_id}`: Abre a radiografia completa do banco vs API.
   - `POST /api/v1/demo/tamper-check`: Simula 3 ataques de adulteração/cópia no banco e mostra o bloqueio em tempo real.
   - `POST /api/v1/demo/crypto-playground`: Teste qualquer valor ao vivo!

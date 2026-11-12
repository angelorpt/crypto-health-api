# ADR 0003: Buscas Exatas em Dados Criptografados via Blind Index (HMAC-SHA256 + Pepper)

* **Status**: Aceito
* **Data**: 2026-11-11

## Contexto

Como o `AES-256-GCM` é probabilístico (cada criptografia gera um texto cifrado diferente), não é possível fazer `SELECT * FROM users WHERE cpf_encrypted = ...` diretamente pelo texto cifrado. Se precisássemos descriptografar todas as linhas da tabela em memória para encontrar um usuário por CPF, e-mail ou tipo sanguíneo, a complexidade seria $O(N)$, inviabilizando o sistema em produção.

## Decisão

Implementamos o padrão **Blind Index (Índice Cego)** utilizando `HMAC-SHA256` com um Pepper dedicado (`APP_BLIND_INDEX_PEPPER`) e separação de domínio por nome do campo:

$$\text{blind\_index} = \text{HMAC-SHA256}(\text{key} = \text{APP\_BLIND\_INDEX\_PEPPER}, \text{msg} = \text{field\_name} \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{normalize}(\text{value}))$$

* Antes do cálculo, o valor é **normalizado** (CPF mantém apenas os 11 dígitos; e-mail é convertido para minúsculas sem espaços; tipo sanguíneo em maiúsculas).
* O resultado hexadecimal de 64 caracteres é salvo em uma coluna indexada ao lado da coluna criptografada (`email_blind_index`, `cpf_blind_index`, `blood_type_blind_index`).

## Consequências

* Buscas exatas por CPF, e-mail e tipo sanguíneo executam em **$O(1)$ / $O(\log N)$** via índice B-Tree do banco de dados, sem descriptografar nenhuma linha irrelevante.
* A restrição `UNIQUE` no banco funciona normalmente sobre `email_blind_index` e `cpf_blind_index`.
* Sem o `APP_BLIND_INDEX_PEPPER` (que fica fora do banco), um invasor que obtenha um dump do SQL não consegue fazer ataques de dicionário/rainbow table contra CPFs ou tipos sanguíneos.

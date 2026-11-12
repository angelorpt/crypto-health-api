# ADR 0004: Hash de Senhas com Argon2id + Salt Aleatório + Server Pepper (HMAC-SHA256)

* **Status**: Aceito
* **Data**: 2026-11-11

## Contexto

Senhas de usuários jamais devem ser criptografadas de forma reversível; devem ser armazenadas usando uma função de hash *memory-hard* resistente a ataques de força bruta em GPUs/ASICs, combinada com um segredo de servidor (*Pepper*).

## Decisão

Utilizamos uma construção em duas etapas em `PasswordCryptoService`:

1. **Pré-Hash com Pepper (HMAC-SHA256)**:
   $$\text{peppered\_password} = \text{HMAC-SHA256}(\text{key} = \text{APP\_PASSWORD\_PEPPER}, \text{msg} = \text{plain\_password})$$
2. **Argon2id com Salt Criptográfico Único (16 bytes)**:
   $$\text{password\_hash} = \text{Argon2id}(\text{peppered\_password}, \text{salt} = \text{random}(16\text{B}), m=19\text{ MiB}, t=2, p=2)$$

## Consequências

* Dois usuários que escolham exatamente a mesma senha possuem hashes Argon2id completamente diferentes no banco (devido ao salt aleatório de 16 bytes embutido na string PHC).
* Caso ocorra vazamento completo da tabela `users`, nenhum hash pode ser quebrado offline sem antes comprometer também o `APP_PASSWORD_PEPPER` armazenado no servidor/KMS.
* O uso de `HMAC-SHA256` na etapa de *peppering* preserva entropia uniforme independentemente do tamanho da senha do usuário.

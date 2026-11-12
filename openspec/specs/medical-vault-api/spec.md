# Especificação: API REST de Usuários, Prontuários e Auditoria Demo (`medical-vault-api`)

## Objetivo

Definir os contratos REST para gerenciamento de usuários, prontuários médicos criptografados e endpoints interativos de demonstração e auditoria criptográfica.

## Requisitos

### Requirement: CRUD e Busca Cega de Usuários e Prontuários
A API SHALL expor rotas em `/api/v1/users` e `/api/v1/medical-records` que recebem dados em texto plano, persistem apenas textos cifrados e Blind Indexes no banco de dados, e retornam os dados descriptografados nas respostas autorizadas.

#### Scenario: Cadastro e leitura de prontuário médico
- **WHEN** um cliente envia `POST /api/v1/users` com dados pessoais e `medical_record` contendo `weight_kg: 80.0` e `height_m: 1.75`
- **THEN** a API SHALL persistir todas as colunas sensíveis criptografadas e retornar `201 Created` com os dados descriptografados e `bmi: 26.12`.

### Requirement: Endpoints de Demonstração e Auditoria Criptográfica
A API SHALL expor rotas sob `/api/v1/demo` para comprovar visualmente a criptografia no banco de dados sem exigir acesso SQL manual ao container.

#### Scenario: Comparação de dados médicos idênticos (`/api/v1/demo/seed-comparison`)
- **WHEN** um cliente chama `POST /api/v1/demo/seed-comparison`
- **THEN** a API SHALL garantir a existência de dois usuários de demonstração com dados médicos idênticos (`80.0 kg`, `1.75 m`, `O+`) e retornar a comparação lado a lado provando que `ciphertexts_are_different` é `true` para todos os campos.

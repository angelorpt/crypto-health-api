# Proposal: Documentação Completa, Diagramas C4/UML e Apresentações Slidev

## Why
O MedVault Crypto API é um projeto de referência e estudo focado em ensinar criptografia aplicada em bancos de dados (PII e dados médicos sob LGPD/CFM). Atualmente, a execução é demonstrada quase exclusivamente via scripts automatizados em `scripts/` (pensados para agentes de IA), sem instruções detalhadas para desenvolvedores realizarem setup, migrações e testes manuais, nem explicação aprofundada dos conceitos de criptografia e engenharia de software (Clean Architecture, SOLID, KISS, DRY) aplicados no código.
Além disso, há a necessidade de material visual de alta qualidade (diagramas no estilo C4 em Mermaid, diagramas de sequência UML detalhados e decks de slides interativos em Slidev) para permitir que desenvolvedores compreendam desde os conceitos mais básicos até a implementação técnica, e possam apresentar esse conhecimento para outras pessoas.

## What Changes
- **Aviso Didático e Quickstart no `README.md`**: Atualização do README principal com aviso explícito de projeto de estudo e instruções de início rápido manual em poucos comandos (usando SQLite padrão e FastAPI).
- **Guia Operacional Manual Completo (`docs/como-executar.md`)**: Passo a passo detalhado cobrindo 4 formas de executar o projeto (SQLite local, PostgreSQL no Docker com API local, Docker Compose completo e scripts automatizados), manipulação do `.env`, geração segura de peppers criptográficos, inspeção manual direta no banco (`sqlite3` e `psql`), testes e solução de problemas.
- **Guia Definitivo de Criptografia (`docs/guia-didatico-criptografia.md`)**: Documento pedagógico completo que parte do absoluto zero (o que é criptografia vs hash vs codificação) e detalha Salt, Pepper, Nonce, os 3 pilares da arquitetura (`HKDF-SHA256`, `AES-256-GCM + AAD`, `Blind Index HMAC`, `Argon2id`), Threat Modeling e conformidade normativa (LGPD, CFM, NIST).
- **Guia de Arquitetura e Engenharia de Software (`docs/arquitetura-engenharia-software.md`)**: Mapeamento prático de Clean Architecture, Clean Code, SOLID, KISS e DRY com trechos de código reais do MedVault.
- **Guia de Conformidade Regulatória (`docs/conformidade-regulatoria.md`)**: Relação detalhada de leis e normas (LGPD Art. 46, CFM 1.821 NGS1/NGS2, SBIS, HIPAA, NIST FIPS 197 / SP 800-38D / SP 800-111, RFCs).
- **Catálogo de Diagramas C4 e UML (`docs/diagramas/`)**:
  - `c4-contexto.md` e visualizador: Diagrama de Contexto de Sistema (C4 Nível 1).
  - `c4-container.md`: Diagrama de Containers (C4 Nível 2 - Cliente, API FastAPI, Motor Cripto, PostgreSQL/SQLite).
  - `c4-componentes.md`: Diagrama de Componentes (C4 Nível 3 - Core Crypto, Services, Repositories, Routers).
  - `sequencia-escrita-leitura.md`: Diagramas de sequência UML detalhando o fluxo de criptografia na escrita e descriptografia na leitura com validação de AAD.
  - `sequencia-blind-index.md`: Diagrama de sequência UML da busca exata em O(1) via HMAC.
- **Decks de Apresentação em Slidev (`docs/slides/`)**:
  - `package.json` configurado para Slidev (@slidev/cli, temas e scripts).
  - `01-criptografia-no-banco.md`: Apresentação focada em Criptografia, Segurança de Dados e LGPD.
  - `02-arquitetura-e-clean-code.md`: Apresentação focada em Engenharia de Software, Clean Architecture e SOLID no MedVault.
  - `README.md` com instruções completas de execução local (`npm run dev`), navegação, zoom e exportação (PDF/SPA).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- None. (Esta change foca em documentação didática, diagramas visuais e apresentações em Slidev, sem alterar o comportamento funcional das APIs existentes).

## Impact
- **Arquivos Criados/Atualizados**: `README.md`, `docs/como-executar.md`, `docs/guia-didatico-criptografia.md`, `docs/arquitetura-engenharia-software.md`, `docs/conformidade-regulatoria.md`, `docs/diagramas/*`, `docs/slides/*`.
- **Código e APIs**: Nenhuma quebra de contrato de API ou alteração de regras de negócio.
- **Dependências**: Adição de dependências Node/NPM isoladas em `docs/slides/package.json` para o Slidev.

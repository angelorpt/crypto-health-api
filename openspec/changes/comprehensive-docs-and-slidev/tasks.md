# Tasks: Documentação Completa, Diagramas C4/UML e Apresentações Slidev

## 1. Guia Operacional Manual e Atualização do README

- [x] 1.1 Criar `docs/como-executar.md` com os 4 caminhos de execução manual (SQLite local, Postgres no Docker com API local, Docker Compose completo, scripts), guia de `.env`, comandos `psql`/`sqlite3` e troubleshooting.
- [x] 1.2 Atualizar `README.md` com badge/aviso de projeto de estudo, quickstart manual em 4 comandos, e índice para as novas documentações e apresentações.
- [x] 1.3 Commit semântico: `docs: adicionar guia operacional manual e atualizar README com quickstart`

## 2. Guias Teóricos e Regulatórios

- [x] 2.1 Criar `docs/guia-didatico-criptografia.md` abordando do zero ao avançado (Criptografia vs Hash vs Codificação, Salt, Pepper, Nonce, HKDF, AES-256-GCM + AAD, HMAC Blind Index, Argon2id e Threat Model).
- [x] 2.2 Criar `docs/arquitetura-engenharia-software.md` detalhando Clean Architecture, Clean Code, SOLID, DRY, KISS e OO com mapeamento no código do MedVault.
- [x] 2.3 Criar `docs/conformidade-regulatoria.md` mapeando LGPD (Art. 46), CFM 1.821 (NGS1/NGS2), SBIS, HIPAA, NIST (FIPS 197, SP 800-38D, SP 800-111) e RFCs.
- [x] 2.4 Commit semântico: `docs: adicionar guias de criptografia, engenharia de software e conformidade regulatoria`

## 3. Catálogo de Diagramas Visuais C4 e UML

- [x] 3.1 Criar `docs/diagramas/c4-contexto.md` com diagrama C4 Nível 1 em Mermaid padrão.
- [x] 3.2 Criar `docs/diagramas/c4-container.md` com diagrama C4 Nível 2 em Mermaid padrão.
- [x] 3.3 Criar `docs/diagramas/c4-componentes.md` com diagrama C4 Nível 3 em Mermaid padrão.
- [x] 3.4 Criar `docs/diagramas/sequencia-escrita-leitura.md` com diagrama de sequência de criptografia/descriptografia com validação de AAD.
- [x] 3.5 Criar `docs/diagramas/sequencia-blind-index.md` com diagrama de sequência de busca exata O(1) via HMAC.
- [x] 3.6 Commit semântico: `docs: adicionar catalogo de diagramas C4 e sequencia UML em mermaid`

## 4. Apresentações Interativas em Slidev

- [x] 4.1 Criar `docs/slides/package.json` e `docs/slides/README.md` com instruções de instalação do Node/NPM, execução local (`npm run dev`), atalhos de navegação, zoom e exportação PDF.
- [x] 4.2 Criar `docs/slides/01-criptografia-no-banco.md` (Apresentação completa de Criptografia, Segurança e LGPD).
- [x] 4.3 Criar `docs/slides/02-arquitetura-e-clean-code.md` (Apresentação completa de Arquitetura, Camadas, SOLID e Clean Code).
- [x] 4.4 Commit semântico: `docs: adicionar apresentacoes interativas em slidev para criptografia e arquitetura`

## 5. Validação e Integração Git

- [x] 5.1 Executar os testes automatizados da aplicação (`pytest`) e linters (`ruff`) para garantir que o ambiente permanece íntegro.
- [ ] 5.2 Retornar à branch `main` e realizar o merge com squash (`git merge --squash docs/comprehensive-knowledge-and-slidev`).
- [ ] 5.3 Realizar commit final consolidado na branch `main`.

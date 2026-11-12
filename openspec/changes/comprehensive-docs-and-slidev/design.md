# Design: Arquitetura de Documentação, Diagramas C4/UML e Apresentações Slidev

## Context
O MedVault Crypto API possui uma implementação sólida em Python 3.11+, FastAPI e SQLAlchemy 2.0 Async, protegendo PII e dados médicos via HKDF, AES-256-GCM, HMAC Blind Index e Argon2id. No entanto, a documentação e apresentações existentes eram resumidas e direcionadas a automações via shell scripts, sem explorar passo a passo o setup manual, a teoria de criptografia do básico ao avançado, os conceitos de Clean Architecture/SOLID/KISS/DRY aplicados no código, e sem diagramas detalhados desacoplados para fácil visualização e zoom.

## Goals / Non-Goals

**Goals:**
- Fornecer um **Guia Manual Operacional (`docs/como-executar.md`)** sem dependência de scripts para desenvolvedores entenderem todo o fluxo de ambiente virtual, variáveis `.env`, migrações, testes e conexão direta ao PostgreSQL/SQLite.
- Atualizar o `README.md` com aviso explícito de caráter didático/estudo e um quickstart direto.
- Criar o **Guia Didático Definitivo de Criptografia (`docs/guia-didatico-criptografia.md`)** cobrindo do zero (o que é criptografia, encoding, hashing) até os detalhes matemáticos e de segurança da implementação (Salt, Pepper, Nonce, HKDF, AES-GCM, AAD, Blind Index, Argon2id, Threat Model).
- Criar o **Guia de Arquitetura e Engenharia de Software (`docs/arquitetura-engenharia-software.md`)** demonstrando a aplicação prática de Clean Architecture, Clean Code, SOLID, DRY, KISS e Orientação a Objetos com referências diretas ao código fonte.
- Documentar a **Conformidade Regulatória (`docs/conformidade-regulatoria.md`)** conectando as leis e normas médicas (LGPD, CFM 1.821 NGS1/NGS2, SBIS, HIPAA, NIST, RFCs) às decisões técnicas do projeto.
- Disponibilizar diagramas visuais desacoplados (`docs/diagramas/`) em Mermaid puro aplicando a hierarquia do modelo C4 (Contexto, Container, Componentes) e diagramas de sequência UML para leitura/escrita e Blind Index, prontos para inspeção em alta resolução e zoom.
- Criar duas apresentações interativas em Slidev (`docs/slides/`): uma voltada a Criptografia e Segurança, e outra voltada a Arquitetura de Software e Código Limpo, com guia de execução e exportação.

**Non-Goals:**
- Alterar a lógica do motor criptográfico em `src/app/core/crypto.py` ou a estrutura do banco de dados (o foco desta change é exclusivamente documentação, diagramação e material didático/slides).
- Integrar um pipeline de CI/CD para deploy dos slides na nuvem (a execução do Slidev e build estático/PDF será local via Node/NPM).

## Decisions

### 1. Formato dos Diagramas C4 em Mermaid Padrão
- **Decisão**: Utilizar a sintaxe padrão de grafos do Mermaid (`flowchart TB` / `flowchart LR`) estilizada com subgraphs, classes e cores para representar C4 (Contexto Nível 1, Container Nível 2 e Componentes Nível 3), em vez da sintaxe experimental `C4Context` do Mermaid.
- **Justificativa**: A sintaxe `C4Context` nativa do Mermaid tem suporte irregular em renderizadores de markdown, quebras visuais e problemas de alinhamento de texto. Grafos padrão do Mermaid oferecem controle total de nós, labels, estilos, bordas e renderizam com perfeição tanto no GitHub/VS Code quanto dentro do Slidev.
- **Alternativas consideradas**: Usar PlantUML (exigiria Java/Graphviz instalado localmente) ou imagens estáticas PNG (dificultaria manutenibilidade e versionamento).

### 2. Diagramas Desacoplados em Arquivos Dedicados (`docs/diagramas/`)
- **Decisão**: Criar cada diagrama em seu próprio arquivo Markdown dedicado, além de incluí-los nos guias e apresentações.
- **Justificativa**: Permite que o apresentador abra cada diagrama isolado em uma aba separada do navegador/VS Code para dar zoom ilimitado e discutir blocos específicos sem poluição visual.

### 3. Duas Apresentações Especializadas em Slidev (`docs/slides/`)
- **Decisão**: Dividir a apresentação em 2 decks distintos:
  1. `01-criptografia-no-banco.md`: Foco em Segurança, Criptografia, Salt, Pepper, AEAD e LGPD.
  2. `02-arquitetura-e-clean-code.md`: Foco em Engenharia de Software, Clean Architecture, SOLID, Design Patterns e Clean Code.
- **Justificativa**: Evita um deck gigantesco e cansativo de mais de 40 slides, permitindo que o apresentador escolha a palestra adequada conforme o público (times de segurança/compliance vs times de desenvolvimento/arquitetura backend).

### 4. Guia de Setup Manual em 4 Caminhos Claros
- **Decisão**: Estruturar `docs/como-executar.md` em 4 cenários autônomos:
  - Caminho 1: Local Rápido com SQLite (Zero dependências externas, ideal para testar a API em 2 minutos).
  - Caminho 2: Híbrido (PostgreSQL em container Docker e FastAPI rodando na máquina host com recarregamento em tempo real).
  - Caminho 3: Totalmente em Docker (Orquestração completa via Docker Compose com migrações automáticas).
  - Caminho 4: Scripts para Agentes de IA / CLI.
- **Justificativa**: Atende tanto quem não tem Docker instalado e quer estudar o Python puro, quanto quem quer simular um ambiente de produção completo com PostgreSQL.

## Risks / Trade-offs

- **[Dependência de Node.js para o Slidev]** → *Mitigação*: O Slidev fica isolado dentro de `docs/slides/` com seu próprio `package.json`. Quem não possui ou não deseja instalar Node.js continua tendo acesso a 100% da documentação e a apresentação anterior em Marp (`docs/apresentacao-slides.md`), além de poder ler os arquivos `.md` dos slides diretamente.
- **[Diagramas extensos em telas menores]** → *Mitigação*: Separação dos diagramas em arquivos individuais no diretório `docs/diagramas/` com links diretos, facilitando abertura em tela cheia e zoom nativo do navegador/leitor Markdown.

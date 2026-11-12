# Apresentações Interativas em Slidev (MedVault Crypto API)

Esta pasta contém dois decks de slides modernos e interativos desenvolvidos em **[Slidev](https://sli.dev/)** para apresentações técnicas, treinamentos corporativos, palestras e aulas.

---

## 📑 Os Dois Decks Disponíveis

| Arquivo de Slides | Tema Principal | Público-Alvo | Porta Padrão |
| :--- | :--- | :--- | :---: |
| [`01-criptografia-no-banco.md`](./01-criptografia-no-banco.md) | **Criptografia, Segurança e LGPD**: O que é criptografia, Salt vs Pepper, Nonce, HKDF, AES-256-GCM + AAD, Blind Index e Argon2id. | Times de Segurança, Compliance, Backend e Devs Iniciantes/Plenos | `:3030` |
| [`02-arquitetura-e-clean-code.md`](./02-arquitetura-e-clean-code.md) | **Engenharia de Software e Clean Code**: Clean Architecture, Camadas, Princípios SOLID, DRY, KISS, Facade e Orientação a Objetos no código real. | Arquitetos de Software, Tech Leads e Desenvolvedores Python | `:3031` |

---

## 🚀 Como Executar Localmente

### Pré-requisito
* **Node.js** `18.0+` (ou `20+`) e **npm** instalados na sua máquina.

### Passo 1: Instalar as Dependências do Slidev
A partir do diretório `docs/slides/`:
```bash
cd docs/slides
npm install
```

### Passo 2: Iniciar a Apresentação Desejada

* **Para rodar o Deck 1 (Criptografia no Banco de Dados)**:
  ```bash
  npm run dev:cripto
  ```
  Acesse no navegador: **`http://localhost:3030`**

* **Para rodar o Deck 2 (Arquitetura, SOLID e Clean Code)**:
  ```bash
  npm run dev:arquitetura
  ```
  Acesse no navegador: **`http://localhost:3031`**

---

## 🔍 Dicas para o Apresentador: Navegação e Zoom

Durante a apresentação no navegador:
* **Modo Apresentador**: Pressione a tecla **`P`** para abrir o painel com cronômetro, anotações de cada slide e visualização do próximo slide.
* **Visão Geral dos Slides**: Pressione a tecla **`O`** (Overview) para visualizar miniatura de todos os slides e pular rapidamente para qualquer seção.
* **Dar Zoom em Diagramas**:
  * Pressione e segure **`Ctrl`** (ou `Cmd`) e use a **roda do mouse** para aproximar qualquer área do slide.
  * Você também pode abrir os diagramas individuais em alta resolução localizados na pasta [`docs/diagramas/`](../diagramas/).
* **Ferramenta de Desenho / Lousa**: Clique no ícone de caneta no canto inferior direito para rabiscar ou destacar partes do código durante a explicação.

---

## 📄 Exportando para PDF ou Site Estático

Se você quiser enviar a apresentação para outras pessoas sem exigir que elas instalem o Node:

```bash
# Exportar para PDF
npm run export:pdf:cripto
npm run export:pdf:arquitetura

# Construir como Single Page Application (SPA) para hospedagem web estática
npm run build:cripto
npm run build:arquitetura
```

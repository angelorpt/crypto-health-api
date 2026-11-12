# Conformidade Regulatória e Legislação de Proteção de Dados

> **Mapeamento de normas brasileiras (LGPD, CFM, SBIS) e internacionais (HIPAA, NIST, RFCs) aplicadas ao MedVault Crypto API.**

Este documento detalha o embasamento legal e normativo que justifica a escolha das primitivas de criptografia em repouso e a arquitetura adotada no projeto.

---

## 🇧🇷 1. Legislação e Normas Brasileiras

### 1.1 LGPD — Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
* **Art. 5º, II (Dado Pessoal Sensível)**: Dados sobre saúde, vida sexual, dado genético ou biométrico são categorizados como dados sensíveis, exigindo maior rigor no tratamento.
* **Art. 46 (Segurança e Boas Práticas)**: *"Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas de destruição, perda, alteração, comunicação ou qualquer forma de tratamento inadequado ou ilícito."*
* **Art. 48 (Comunicação de Incidentes)**: A ANPD avalia a gravidade do incidente e as medidas técnicas adotadas pelo controlador. **Dados que vazam criptografados com algoritmo robusto (AES-256) reduzem drasticamente o risco de dano relevante aos titulares**.

### 1.2 Resolução CFM nº 1.821/2007 (Conselho Federal de Medicina)
* Aprova as normas técnicas concernentes à digitalização e uso dos sistemas informatizados para a guarda e manuseio dos documentos dos prontuários dos pacientes.
* Estabelece os **Níveis de Garantia de Segurança (NGS)**:
  * **NGS1**: Requisitos de autenticação, controle de acesso e sigilo.
  * **NGS2**: Exige assinatura digital padrão ICP-Brasil para eliminação do suporte de papel e auditoria estrita de integridade.

### 1.3 Manual de Certificação SBIS/CFM (S-RES)
* Elaborado pela Sociedade Brasileira de Informática em Saúde (SBIS) em parceria com o CFM.
* Define os requisitos de segurança obrigatórios para Sistemas de Registro Eletrônico em Saúde (S-RES):
  * **Requisito de Confidencialidade**: Criptografia de dados armazenados para impedir visualização direta no banco de dados.
  * **Requisito de Integridade**: Garantia de que nenhuma alteração não autorizada ocorra nos registros clínicos (atendido no projeto via `AEAD/AES-256-GCM` com tag de 128 bits e AAD).

### 1.4 Lei nº 13.787/2018 (Digitalização e Prontuários Eletrônicos)
* Exige a guarda dos prontuários médicos pelo prazo mínimo de **20 anos** a partir do último registro, tornando obrigatória a garantia de longevidade, autenticidade e sigilo das informações no banco de dados.

---

## 🌎 2. Padrões Internacionais de Referência

### 2.1 HIPAA Security Rule (45 CFR §164.312 — EUA)
* **Encryption and Decryption (§164.312(a)(2)(iv))**: Implementa mecanismos para cifrar e decifrar *Protected Health Information (PHI)* em repouso.
* O MedVault adota conformidade com o princípio de *Safe Harbor* do HITECH Act: se um banco de dados cifrado for comprometido, não há exposição de PHI legível.

### 2.2 ISO/IEC 27001 & ISO 27799 (Segurança da Informação na Saúde)
* A norma **ISO 27799** adapta os controles da ISO/IEC 27002 especificamente para o setor de saúde, destacando o controle de dados criptografados em repouso para proteção de prontuários.

---

## 🔬 3. Normas Técnicas e RFCs Implementadas no MedVault

| Componente no MedVault | Padrão Internacional | Descrição Técnica |
| :--- | :--- | :--- |
| **Criptografia Simétrica** | **NIST FIPS 197** | Advanced Encryption Standard (AES) com chaves de 256 bits. |
| **Modo de Operação e Autenticação** | **NIST SP 800-38D** | Galois/Counter Mode (GCM) com Nonce aleatório de 96 bits e Auth Tag de 128 bits. |
| **Proteção de Contexto (AAD)** | **NIST SP 800-38D (§5.2.1)** | Associated Authenticated Data amarrando `user_id` e `field_name` ao lacre criptográfico. |
| **Derivação de Chave por Usuário** | **RFC 5869 / NIST SP 800-56C** | HMAC-based Extract-and-Expand Key Derivation Function (`HKDF-SHA256`). |
| **Blind Index (Busca Cega)** | **RFC 2104 / FIPS 198-1** | Keyed-Hashing for Message Authentication (`HMAC-SHA256`). |
| **Hash de Senhas** | **RFC 9106 / OWASP** | Argon2id com parâmetros recomendados contra ataques por GPU/ASIC. |
| **Diretrizes de Criptografia em Repouso** | **NIST SP 800-111** | Guide to Storage Encryption Technologies for End User Devices and Servers. |

# Guia de Formatação ABNT — TCC MLOps

Guia completo e verificável para montar o documento final no Word.  
Baseado em: ABNT NBR 14724:2011 (monografia/TCC) e ABNT NBR 6022:2018 (artigo científico).  
Gerado em: 2026-06-22

---

## 0. Tipo de documento e norma aplicável

Este TCC é entregue como **artigo científico** (7–15 páginas) embrulhado em uma **capa de monografia**. Os dois têm normas distintas:

| Parte | Norma | Aplica-se a |
|-------|-------|-------------|
| Capa, folha de rosto, aprovação, listas | ABNT NBR 14724:2011 | Elementos pré-textuais da monografia |
| Resumo / Abstract | ABNT NBR 6028:2003 | Texto do resumo |
| Corpo do artigo (seções 1–7) | ABNT NBR 6022:2018 | Introdução → Conclusão |
| Citações no texto | ABNT NBR 10520:2002 | Todo o artigo |
| Lista de referências | ABNT NBR 6023:2018 | Seção final |

> Se a instituição (MAFRA) exigir template próprio, as instruções abaixo servem como base — priorize o template institucional quando houver conflito.

---

## 1. Configurações do Word (aplicar antes de digitar)

### 1.1 Página
| Parâmetro | Valor |
|-----------|-------|
| Tamanho | A4 (21 × 29,7 cm) |
| Margem superior | 3 cm |
| Margem inferior | 2 cm |
| Margem esquerda | 3 cm |
| Margem direita | 2 cm |

### 1.2 Fonte e parágrafo (corpo do texto)
| Parâmetro | Valor |
|-----------|-------|
| Fonte | Times New Roman ou Arial |
| Tamanho | 12 pt |
| Espaçamento entre linhas | 1,5 |
| Alinhamento | Justificado |
| Recuo de parágrafo | 1,25 cm (primeira linha) |
| Espaço antes/depois do parágrafo | 0 pt |

### 1.3 Exceções de formatação
| Elemento | Fonte | Tamanho | Espaçamento |
|----------|-------|---------|-------------|
| Títulos de seção (1, 2, 3…) | mesma fonte | 12 pt | 1,5 |
| Notas de rodapé | mesma fonte | 10 pt | simples |
| Citações longas (>3 linhas) | mesma fonte | 10 pt | simples |
| Referências bibliográficas | mesma fonte | 12 pt | simples (cada ref.) |
| Legenda de tabelas/figuras | mesma fonte | 10 pt | simples |
| Fonte das tabelas/figuras | mesma fonte | 10 pt | simples |

---

## 2. Estrutura completa do documento final (ordem exata)

### Pré-textuais (não têm numeração de seção, não contam na paginação exibida)

```
[CAPA]
[FOLHA DE ROSTO]
[FOLHA DE APROVAÇÃO]
[DEDICATÓRIA]          ← opcional
[AGRADECIMENTOS]       ← opcional
[EPÍGRAFE]             ← opcional
[RESUMO]               ← resumo-abstract.md
[ABSTRACT]             ← resumo-abstract.md
[LISTA DE FIGURAS]     ← ver Seção 6 deste guia
[LISTA DE TABELAS]     ← ver Seção 7 deste guia
[LISTA DE ABREVIATURAS E SIGLAS]  ← ver Seção 8 deste guia
[SUMÁRIO]              ← gerado automaticamente pelo Word
```

### Textuais (numeração começa em 1)

```
1  INTRODUÇÃO
2  PROBLEMA E OBJETIVOS
   2.1  Problema de Pesquisa
   2.2  Objetivos
3  REFERENCIAL TEÓRICO
   3.1  [título atual da seção 3.1]
   3.2  [título atual da seção 3.2]
   3.3  [título atual da seção 3.3]
   3.4  [título atual da seção 3.4]
4  METODOLOGIA                           ← secao-metodologia-expandida.md
   4.1  Levantamento Bibliográfico
   4.2  Projeto e Desenvolvimento da Infraestrutura
   4.3  Implementação dos Pipelines
        4.3.1  Trilha CI/CD — AWS CodeBuild
        4.3.2  Trilha CT — Treinamento Contínuo (event-driven)
        4.3.3  Trilha de Inferência — FastAPI + EKS + KEDA
   4.4  Validação Experimental
5  MODELAGEM DA SOLUÇÃO
   5.1  Descrição da Abordagem            ← correcoes-artigo.md (Correção 2)
   5.2  Diagrama de Arquitetura Técnica   ← diagrama-arquitetura.md
6  RESULTADOS E DISCUSSÃO                ← secao-resultados-discussao.md
   6.1  Metodologia dos Testes de Carga
   6.2  Resultados dos Testes Locust (Carga Concorrente)
   6.3  Investigação e Correção: O Problema de Cold Start por Ausência de HTTP Keepalive
   6.4  Resultados no Ambiente de Staging
   6.5  Consolidação e Validação do SLA
   6.6  Discussão
7  CONCLUSÃO E TRABALHOS FUTUROS         ← secao-conclusao-trabalhos-futuros.md
   7.1  Conclusão
   7.2  Contribuições
   7.3  Limitações
   7.4  Trabalhos Futuros
```

### Pós-textuais (sem numeração de seção)

```
REFERÊNCIAS             ← correcoes-artigo.md (16 refs)
[APÊNDICES]             ← opcional
[ANEXOS]                ← opcional
```

---

## 3. Correção de numeração urgente

Os arquivos gerados neste projeto usam numerações temporárias que **devem ser renumeradas** ao montar o Word:

| Arquivo | Seção no arquivo | Seção correta no Word |
|---------|-----------------|----------------------|
| `secao-resultados-discussao.md` | "7 RESULTADOS E DISCUSSÃO" | **6 RESULTADOS E DISCUSSÃO** |
| `secao-resultados-discussao.md` | "7.1", "7.2", … "7.6" | **6.1", "6.2", … "6.6"** |
| `secao-conclusao-trabalhos-futuros.md` | "8 CONCLUSÃO E TRABALHOS FUTUROS" | **7 CONCLUSÃO E TRABALHOS FUTUROS** |
| `secao-conclusao-trabalhos-futuros.md` | "8.1", "8.2", "8.3", "8.4" | **7.1", "7.2", "7.3", "7.4"** |
| Qualquer cruzamento interno | "Seção 7" referenciando resultados | **"Seção 6"** |
| `secao-resultados-discussao.md` | nota: "Os resultados são apresentados na Seção 7" | **"Seção 6"** |

Além disso: **REFERÊNCIAS não recebe número de seção** per ABNT — retirar o "6" se houver.

---

## 4. Formatação dos títulos de seção

### 4.1 Estilos no Word

| Nível | Exemplo | Formatação |
|-------|---------|------------|
| Capítulo (1º nível) | `1 INTRODUÇÃO` | Maiúsculas, negrito, 12 pt, alinhado à esquerda |
| Seção (2º nível) | `1.1 Subtítulo` | Título capitalizado, negrito, 12 pt |
| Subseção (3º nível) | `1.1.1 Sub-subtítulo` | Título capitalizado, itálico ou negrito (conforme template) |
| Sem indicativo | `RESUMO`, `REFERÊNCIAS` | Maiúsculas, negrito, centralizado, sem número |

### 4.2 Espaçamento antes e depois dos títulos
- Antes do título de capítulo: 1 linha em branco (ou "Espaço antes" = 12 pt no Word)
- Depois do título de capítulo: sem linha em branco — o texto começa imediatamente
- Entre parágrafos: sem linha em branco (o recuo de 1,25 cm distingue os parágrafos)

---

## 5. Formatação de citações no texto (ABNT NBR 10520:2002)

### 5.1 Citações indiretas (paráfrase) — já usadas no artigo
Formato correto (verificado): `(SOBRENOME, ano)` ou `Sobrenome (ano)`

Exemplos já corretos no artigo:
- `(SCULLEY et al., 2015)` ✓
- `(ZAHARIA et al., 2018)` ✓
- `(BRIKMAN, 2019; KARIMIBIUKI et al., 2022)` ✓ — múltiplas refs: separar com ponto e vírgula, ordem alfabética

### 5.2 Citações diretas curtas (até 3 linhas)
Inserir entre aspas duplas no corpo do texto:
```
"[texto citado]" (SOBRENOME, ano, p. X)
```

### 5.3 Citações diretas longas (mais de 3 linhas)
Bloco separado do parágrafo:
- Recuo esquerdo: 4 cm
- Fonte: 10 pt
- Espaçamento: simples
- Sem aspas
- Fonte após o bloco: `(SOBRENOME, ano, p. X)`

### 5.4 Verificação de citações no artigo — ação necessária

Percorrer o artigo completo e verificar:
- [ ] Toda afirmação factual de outro autor tem citação?
- [ ] Citações com `et al.` têm 3 ou mais autores no original? (ABNT: usar `et al.` para 3+ autores)
- [ ] Citações de sites têm "Acesso em: [data]"?
- [ ] Referências ao MLflow → citar `(ZAHARIA et al., 2018)` ✓
- [ ] Referências ao Terraform → citar `(BRIKMAN, 2019)` ✓
- [ ] Referências a Kubernetes/EKS → citar `(HIGHTOWER; BURNS; BEDA, 2022)` ✓
- [ ] Referências a CI/CD → citar `(HUMBLE; FARLEY, 2010)` ou `(KIM et al., 2016)` ✓
- [ ] Referências a DevOps → citar `(KIM et al., 2016)` ✓
- [ ] Referências a concept drift → citar `(GAMA et al., 2014)` ✓
- [ ] Referências ao Amazon Bedrock → citar `(AWS, 2026)` ✓

---

## 6. Lista de Figuras

Inserir após o Abstract, antes das Listas de Tabelas.

```
LISTA DE FIGURAS

Figura 1 — Arquitetura da Plataforma MLOps ........................................ [página]
```

**Legenda abaixo de cada figura no texto** (ABNT NBR 6022:2018):
```
Figura 1 — Arquitetura da Plataforma MLOps
[imagem]
Fonte: elaboração do autor.
```

- Título acima da figura: "Figura N — Título", 10 pt, centralizado
- Fonte abaixo da figura: "Fonte: elaboração do autor.", 10 pt, centralizado
- A figura deve estar inserida no Word como imagem (não texto)
- Referência no texto: "conforme ilustrado na Figura 1" ou "(ver Figura 1)"

---

## 7. Lista de Tabelas

Inserir após a Lista de Figuras.

```
LISTA DE TABELAS

Tabela 1  — Sequência de Stacks e Responsabilidades ................................ [página]
Tabela 2  — Configuração do ScaledObject KEDA (DEV) ................................ [página]
Tabela 3  — Cenários de Validação Experimental ...................................... [página]
Tabela 4  — Critérios de Aceitação SLA .............................................. [página]
Tabela 5  — Comparativo Antes × Após Otimização de Keepalive (DEV) .................. [página]
Tabela 6  — Latências Sequenciais Antes e Após Keepalive (DEV, 100 req.) ............. [página]
Tabela 7  — Latências Sequenciais no Ambiente Staging (100 req.) ..................... [página]
Tabela 8  — Validação Final do SLA .................................................. [página]
```

**Legenda acima de cada tabela no texto** (ABNT):
```
Tabela N — Título da Tabela
[tabela]
Fonte: elaboração do autor. / Fonte: [origem dos dados], adaptado pelo autor.
```

- Título **acima** da tabela: "Tabela N — Título", 10 pt, alinhado à esquerda (ou centralizado conforme template)
- Fonte **abaixo** da tabela: 10 pt
- Tabelas 5–8: Fonte → `Fonte: dados da pesquisa, 2026.`
- Tabelas 1–4: Fonte → `Fonte: elaboração do autor.`

**Renumeração das tabelas da Seção 6 (Resultados):**

Os arquivos gerados na Task #18 nomeiam as tabelas como Tabela 1–4. Com as tabelas da Metodologia (4.2, 4.3.3, 4.4), elas passam a ser Tabela 5–8. Ao montar o Word, renumerar conforme a lista acima.

---

## 8. Lista de Abreviaturas e Siglas

Inserir após a Lista de Tabelas. Formato: abreviatura à esquerda, definição à direita, alinhada com tabulação.

```
LISTA DE ABREVIATURAS E SIGLAS

3DS     Three Domain Secure (protocolo de autenticação de transações)
ALB     Application Load Balancer
API     Application Programming Interface (Interface de Programação de Aplicações)
ARN     Amazon Resource Name
AWS     Amazon Web Services
CI      Continuous Integration (Integração Contínua)
CD      Continuous Delivery (Entrega Contínua)
CI/CD   Continuous Integration and Continuous Delivery
CT      Continuous Training (Treinamento Contínuo)
ECR     Elastic Container Registry
EKS     Elastic Kubernetes Service
ETL     Extract, Transform, Load
HTTP    Hypertext Transfer Protocol
HPA     Horizontal Pod Autoscaler
IaC     Infrastructure as Code (Infraestrutura como Código)
IAM     Identity and Access Management
JSON    JavaScript Object Notation
KEDA    Kubernetes Event-Driven Autoscaling
LLM     Large Language Model (Modelo de Linguagem de Grande Escala)
ML      Machine Learning (Aprendizado de Máquina)
MLOps   Machine Learning Operations
NLB     Network Load Balancer
PDB     Pod Disruption Budget
REST    Representational State Transfer
RPS     Requests Per Second (Requisições por Segundo)
SLA     Service Level Agreement (Acordo de Nível de Serviço)
SQS     Simple Queue Service
TCC     Trabalho de Conclusão de Curso
TCP     Transmission Control Protocol
VPC     Virtual Private Cloud
YAML    YAML Ain't Markup Language
```

---

## 9. Referências bibliográficas (ABNT NBR 6023:2018)

As 16 referências em formato ABNT pronto para copiar na seção REFERÊNCIAS.  
Ordem: **alfabética pelo sobrenome do primeiro autor**.

---

AMAZON WEB SERVICES (AWS). *Amazon Bedrock User Guide*. Disponível em: https://docs.aws.amazon.com/bedrock/. Acesso em: jun. 2026.

AMAZON WEB SERVICES (AWS). *Machine Learning Lens — AWS Well-Architected Framework*. Disponível em: https://docs.aws.amazon.com/wellarchitected/. Acesso em: mar. 2026.

BRECK, Eric; CAIN, Shanqing; NIELSEN, Eric; SALIB, Michael; SCULLEY, David. The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction. In: IEEE INTERNATIONAL CONFERENCE ON BIG DATA (BIG DATA), 5., 2017, Boston. *Anais* [...]. Piscataway: IEEE, 2017. p. 1123–1132.

BRIKMAN, Yevgeniy. *Terraform: Up & Running: Writing Infrastructure as Code*. 2. ed. Sebastopol: O'Reilly Media, 2019.

FOWLER, Martin. *Continuous Integration*. MartinFowler.com, 2006. Disponível em: https://martinfowler.com/articles/continuousIntegration.html. Acesso em: mar. 2026.

GAMA, João; ŽLIOBAITĖ, Indrė; BIFET, Albert; PECHENIZKIY, Mykola; BOUCHACHIA, Abdelhamid. A Survey on Concept Drift Adaptation. *ACM Computing Surveys*, v. 46, n. 4, artigo 44, p. 1–37, abr. 2014.

GOOGLE CLOUD. *MLOps: Continuous delivery and automation pipelines in machine learning*. Google Cloud Architecture Center, 2023. Disponível em: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning. Acesso em: mar. 2026.

HIGHTOWER, Kelsey; BURNS, Brendan; BEDA, Joe. *Kubernetes: Up and Running: Dive into the Future of Infrastructure*. 3. ed. Sebastopol: O'Reilly Media, 2022.

HUMBLE, Jez; FARLEY, David. *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Boston: Addison-Wesley Professional, 2010.

KARIMIBIUKI, M.; KAUR, A.; DAVE, V.; ADAMS, B.; BEZEMER, C.-P. Drifted and Not Fixed: An Empirical Study of Configuration Drift in Continuous Deployment. In: IEEE INTERNATIONAL CONFERENCE ON SOFTWARE MAINTENANCE AND EVOLUTION (ICSME), 2022, Limassol. *Anais* [...]. Piscataway: IEEE, 2022.

KIM, Gene; HUMBLE, Jez; DEBOIS, Patrick; WILLIS, John. *The DevOps Handbook: How to Create World-Class Agility, Reliability, and Security in Technology Organizations*. Portland: IT Revolution Press, 2016.

KREUZBERGER, Dominik; KÜHL, Niklas; HIRSCHL, Sebastian. Machine Learning Operations (MLOps): Overview, Definition, and Architecture. *IEEE Access*, v. 11, p. 31866–31879, 2023.

MÄKINEN, Sami; SKÖN, Jukka-Pekka; MIKKONEN, Tommi; SYSTÄ, Kari. Who Needs MLOps: What Data Scientists Seek to Accomplish and How Can MLOps Help? In: IEEE/ACM INTERNATIONAL WORKSHOP ON COOPERATIVE AND HUMAN ASPECTS OF SOFTWARE ENGINEERING (CHASE), 2021, Madrid. *Anais* [...]. Piscataway: IEEE, 2021. p. 109–112.

SCULLEY, D.; HOLT, Gary; GOLOVIN, Daniel; DAVYDOV, Eugene; PHILLIPS, Todd; EBNER, Dietmar; CHAUDHARY, Vinay; YOUNG, Michael; CRESPO, Jean-François; DENNISON, Dan. Hidden Technical Debt in Machine Learning Systems. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 28., 2015, Montreal. *Anais* [...]. Red Hook: Curran Associates, 2015. p. 2503–2511.

TREVEIL, Mark; OMONT, Nicolas; STENAC, Clément; LEFEVRE, Kenji; PUY, Du; PALM, Joachim; SHARP, Lynn. *Introducing MLOps: How to Scale Machine Learning in the Enterprise*. Sebastopol: O'Reilly Media, 2020.

ZAHARIA, Matei; CHEN, Andrew; DAVIDSON, Aaron; GHODSI, Ali; HONG, Sue Ann; MURTHY, Andy; XING, Andy; CHEN, Richard; ROSENTHAL, Zach; YAVUZ, Burak; SHENKER, Scott. Accelerating the Machine Learning Lifecycle with MLflow. *IEEE Data Engineering Bulletin*, v. 41, n. 4, p. 39–45, dez. 2018.

---

### 9.1 Verificação de pontos críticos nas referências

| # | Autores | Tipo | Verificação |
|---|---------|------|------------|
| AWS Bedrock | AWS | Website | ✓ Tem "Acesso em: jun. 2026" |
| AWS Well-Arch. | AWS | Website | ✓ Tem "Acesso em: mar. 2026" |
| BRECK et al. | 5 autores | Anais | ✓ Tem todos os nomes (não usa "et al." na referência) |
| BRIKMAN | 1 autor | Livro | ✓ |
| FOWLER | 1 autor | Website | ✓ Tem URL e "Acesso em" |
| GAMA et al. | 5 autores | Periódico | ✓ Tem v., n., p., mês, ano |
| GOOGLE CLOUD | Inst. | Website | ✓ Tem URL e "Acesso em" |
| HIGHTOWER et al. | 3 autores | Livro | ✓ Separar com ponto e vírgula no texto: `(HIGHTOWER; BURNS; BEDA, 2022)` |
| HUMBLE; FARLEY | 2 autores | Livro | ✓ No texto: `(HUMBLE; FARLEY, 2010)` |
| KARIMIBIUKI et al. | 5 autores | Anais | ⚠ Verificar se o texto usa "KA-RIMIBIUKI" (hifenizado) ou "KARIMIBIUKI" — padronizar |
| KIM et al. | 4 autores | Livro | ✓ No texto: `(KIM et al., 2016)` |
| KREUZBERGER et al. | 3 autores | Periódico | ✓ |
| MÄKINEN et al. | 4 autores | Anais | ✓ Atenção ao "Ä" no sobrenome |
| SCULLEY et al. | 10 autores | Anais | ✓ No texto: `(SCULLEY et al., 2015)` |
| TREVEIL et al. | 7 autores | Livro | ✓ |
| ZAHARIA et al. | 9 autores | Periódico | ✓ |

---

## 10. Numeração de páginas no Word

### 10.1 Regra ABNT
- **Contagem começa** na folha de rosto (página 1), mas os números só são **exibidos** a partir da primeira página do texto (Introdução)
- **Posição:** canto superior direito da página (sem "p." ou "pág.")
- Elementos pré-textuais (Resumo, Abstract, Listas, Sumário): **contados mas não numerados visivelmente**

### 10.2 Como fazer no Word
1. Inserir quebra de seção (**Continuous Section Break**) antes da Introdução
2. Na seção do texto, desmarcar **"Link to Previous"** no cabeçalho/rodapé
3. Inserir número de página na seção do texto
4. Na seção dos pré-textuais, inserir número de página com **formato "i, ii, iii"** (romano) ou sem número visível
5. Definir o **número inicial** da seção de texto de forma que corresponda à contagem real da folha de rosto

---

## 11. Capa e Folha de Rosto (ABNT NBR 14724:2011)

### 11.1 Capa (obrigatória)
```
[logo da instituição — centro]

[nome da instituição — maiúsculas, centro]
[nome do curso — maiúsculas, centro]

[nome completo do autor — maiúsculas, centro]


[título do trabalho — maiúsculas, negrito, centro]
[subtítulo se houver]


[cidade]
[ano]
```

**Dados para esta capa:**
- Instituição: [nome completo da faculdade em Mafra]
- Curso: Engenharia de Software
- Autor: GUSTAVO LIEBL PEREIRA
- Título: INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS PRÁTICAS PARA ENTREGA CONTÍNUA DE MODELOS DE MACHINE LEARNING EM PRODUÇÃO
- Cidade: Mafra
- Ano: 2026

### 11.2 Folha de Rosto (obrigatória)
```
[nome do autor — centro]


[título — maiúsculas, negrito, centro]


                    [nota de natureza — alinhada ao centro direito, 10 pt, 8 cm de recuo]
                    Trabalho de Conclusão de Curso apresentado ao
                    Curso de Engenharia de Software da [nome da
                    instituição] como requisito parcial para obtenção
                    do título de Bacharel em Engenharia de Software.

                    Orientador: Prof. Marcelo Semmer


[cidade]
[ano]
```

### 11.3 Folha de Aprovação (obrigatória)
```
[nome do autor]

[título]

Trabalho de Conclusão de Curso apresentado ao Curso de Engenharia de Software
da [instituição] como requisito parcial para obtenção do título de Bacharel em
Engenharia de Software, aprovado pela Banca Examinadora formada por:

Mafra, ____ de ____________ de 2026.


________________________________________
Prof. Marcelo Semmer
Orientador — [instituição]

________________________________________
Prof. [Nome do Avaliador 2]
[Instituição]

________________________________________
Prof. [Nome do Avaliador 3]
[Instituição]
```

---

## 12. Sumário (gerado automaticamente no Word)

Para gerar o sumário automaticamente:
1. Aplicar estilos **Heading 1**, **Heading 2**, **Heading 3** nos títulos de seção
2. Referências → Insert Table of Contents
3. Incluir apenas os 3 primeiros níveis
4. Verificar que "REFERÊNCIAS", "RESUMO", "ABSTRACT" aparecem **sem número** no sumário

**Preview do Sumário:**
```
RESUMO ........................................................................  ii
ABSTRACT .....................................................................  iii
LISTA DE FIGURAS .............................................................  iv
LISTA DE TABELAS .............................................................   v
LISTA DE ABREVIATURAS E SIGLAS ...............................................  vi

1  INTRODUÇÃO ................................................................   1
2  PROBLEMA E OBJETIVOS ......................................................   2
   2.1  Problema de Pesquisa .................................................   2
   2.2  Objetivos ............................................................   2
3  REFERENCIAL TEÓRICO .......................................................   3
4  METODOLOGIA ...............................................................   5
   4.1  Levantamento Bibliográfico ...........................................   5
   4.2  Projeto e Desenvolvimento da Infraestrutura ..........................   5
   4.3  Implementação dos Pipelines ..........................................   6
   4.4  Validação Experimental ...............................................   8
5  MODELAGEM DA SOLUÇÃO ......................................................   9
   5.1  Descrição da Abordagem ...............................................   9
   5.2  Diagrama de Arquitetura Técnica ......................................  10
6  RESULTADOS E DISCUSSÃO ....................................................  11
7  CONCLUSÃO E TRABALHOS FUTUROS .............................................  14
REFERÊNCIAS ..................................................................  16
```

---

## 13. Itálico e negrito no texto

| Caso | Formatação | Exemplo |
|------|------------|---------|
| Termos em inglês não incorporados ao português | Itálico | *machine learning*, *keepalive*, *pods* |
| Termos técnicos consagrados (uso geral) | Normal (sem itálico) | MLOps, DevOps, Docker, Kubernetes |
| Nomes de ferramentas e serviços | Normal | AWS, Terraform, MLflow, FastAPI, KEDA |
| Destaque de termos definidos pela primeira vez | Negrito ou itálico | **concept drift**, *throughput* |
| Títulos de obras nas referências | **Negrito** | *Terraform: Up & Running* → colocar em negrito |

> ABNT NBR 6023:2018: o título da obra deve estar em **negrito** nas referências (não em itálico).

---

## 14. Checklist final antes de entregar

### Pré-textuais
- [ ] Capa com dados completos (instituição, curso, autor, título, cidade, ano)
- [ ] Folha de rosto com nota de natureza e orientador
- [ ] Folha de aprovação (pode ser entregue sem assinaturas, para completar após a banca)
- [ ] Resumo: parágrafo único, sem citações, com "Palavras-chave:" ao final
- [ ] Abstract: tradução fiel do Resumo, com "Keywords:" ao final
- [ ] Lista de Figuras completa e com páginas
- [ ] Lista de Tabelas com 8 entradas e páginas
- [ ] Lista de Abreviaturas em ordem alfabética
- [ ] Sumário com todos os títulos e páginas corretas (atualizar depois da montagem)

### Corpo do artigo
- [ ] Seção 4 substituída pela versão expandida (`secao-metodologia-expandida.md`)
- [ ] Seção 5.1 com as duas correções de `correcoes-artigo.md`
- [ ] Seção 5.2 com o diagrama atualizado de `diagrama-arquitetura.md`
- [ ] Seção 6 inserida após 5.2 (`secao-resultados-discussao.md`)
- [ ] Seção 7 inserida após 6 (`secao-conclusao-trabalhos-futuros.md`)
- [ ] Seções 6 e 7 renumeradas (de 7/8 para 6/7 conforme Seção 3 deste guia)
- [ ] Tabelas da Seção 6 renumeradas (de Tabela 1–4 para Tabela 5–8)
- [ ] Todas as tabelas têm: título acima (10 pt) + fonte abaixo (10 pt)
- [ ] Figura 1 tem: título acima + fonte abaixo ("elaboração do autor")
- [ ] "estudo de caso" substituído por "projeto implementado em ambiente de produção" em todo o artigo
- [ ] "GitHub Actions" corrigido para "AWS CodeBuild" em todo o artigo
- [ ] Referências cruzadas entre seções usam os números corretos

### Referências
- [ ] 16 referências em ordem alfabética
- [ ] Títulos de obras em **negrito** (não itálico)
- [ ] Websites têm "Disponível em:" e "Acesso em:"
- [ ] KARIMIBIUKI padronizado (sem hifenização)
- [ ] Espaçamento simples entre linhas dentro de cada referência
- [ ] Linha em branco entre referências

### Formatação geral
- [ ] Margens: 3/2/3/2 cm (sup/inf/esq/dir)
- [ ] Fonte 12 pt, espaçamento 1,5, justificado em todo o corpo
- [ ] Recuo de parágrafo 1,25 cm
- [ ] Numeração de páginas no canto superior direito
- [ ] Títulos de capítulo: maiúsculas, negrito
- [ ] "REFERÊNCIAS" sem número de seção

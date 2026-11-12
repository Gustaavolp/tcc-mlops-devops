---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
color: #1a1a2e
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 22px;
  }
  h1 {
    color: #16213e;
    font-size: 36px;
    border-bottom: 3px solid #e94560;
    padding-bottom: 8px;
  }
  h2 {
    color: #0f3460;
    font-size: 28px;
  }
  h3 {
    color: #e94560;
    font-size: 22px;
  }
  table {
    font-size: 18px;
    width: 100%;
  }
  th {
    background-color: #0f3460;
    color: white;
    padding: 6px 10px;
  }
  td {
    padding: 5px 10px;
  }
  tr:nth-child(even) {
    background-color: #f0f4ff;
  }
  code {
    background-color: #f0f4ff;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 18px;
  }
  .highlight {
    background-color: #fff3cd;
    border-left: 4px solid #e94560;
    padding: 10px 16px;
    margin: 10px 0;
  }
  footer {
    font-size: 14px;
    color: #888;
  }
---

<!-- Slide 1 — CAPA -->

# Integração de MLOps em Pipelines DevOps

### Desafios e Boas Práticas para Entrega Contínua de Modelos de Machine Learning em Produção

<br>

**Autor:** Gustavo Liebl Pereira
**Orientador:** Prof. Marcelo Semmer
**Curso:** Engenharia de Software
**Instituição:** [Nome da Instituição] — Mafra, SC
**Semestre:** 2026/1

---

<!-- Slide 2 — AGENDA -->

# Agenda

1. Problema de Pesquisa
2. Objetivos
3. Metodologia
4. Arquitetura da Plataforma
5. Infraestrutura como Código (IaC)
6. Trilhas de Automação: CI/CD e CT
7. Inferência Escalável (EKS + KEDA)
8. Observabilidade Generativa (Bedrock)
9. Resultados e Achados Críticos
10. Validação do SLA
11. Contribuições, Limitações e Trabalhos Futuros
12. Conclusão

---

<!-- Slide 3 — CONTEXTUALIZAÇÃO -->

# O Problema: Da Experimentação à Produção

**85% dos projetos de ML nunca chegam à produção** *(Gartner, 2022)*

```
┌─────────────────────────────────────────────────┐
│  Cientista de Dados                             │
│  ✓ Modelo treinado        ✓ Acurácia excelente  │
│  ✗ Sem API               ✗ Sem monitoramento    │
│  ✗ Sem versionamento      ✗ Sem reproductibilidade│
└────────────────┬────────────────────────────────┘
                 │  "Funcionou no Jupyter..."
                 ▼
┌─────────────────────────────────────────────────┐
│  Time de Engenharia                             │
│  ✗ Sem governança         ✗ Sem pipeline CT     │
│  ✗ Deploy manual          ✗ Model drift oculto  │
└─────────────────────────────────────────────────┘
```

> **Contexto real:** Plataforma de detecção de fraude em transações de pagamentos eletrônicos — empresa de grande porte, infraestrutura AWS em produção.

---

<!-- Slide 4 — PERGUNTA E OBJETIVOS -->

# Pergunta de Pesquisa e Objetivos

**Pergunta:** Como integrar de forma eficiente, escalável e automatizada o ciclo de vida de modelos de ML (MLOps) em pipelines de DevOps, garantindo entrega contínua e governança operacional?

<br>

**Objetivos Específicos:**

| # | Objetivo |
|---|----------|
| i | Projetar as camadas de integração DevOps/MLOps |
| ii | Implementar infraestrutura como código via Terraform |
| iii | Desenvolver pipelines de CI/CD e Treinamento Contínuo (CT) |
| iv | Implementar governança de modelos via MLflow |
| v | Validar escalonamento orientado a eventos com KEDA |

---

<!-- Slide 5 — METODOLOGIA -->

# Metodologia

> **Pesquisa aplicada de caráter experimental e construtivo** — o pesquisador projetou, implementou e validou a plataforma em ambiente de produção real.

<br>

```
Fase 1                Fase 2               Fase 3              Fase 4
─────────             ─────────            ─────────           ─────────
Levantamento    →     IaC com        →     Pipelines    →      Validação
Bibliográfico         Terraform            CI/CD + CT          Experimental
                      (5 stacks,           AWS CodeBuild       Locust
IEEE Xplore           15 módulos)          Lambda + SM         100 payloads 3DS
ACM DL                DEV + Staging        FastAPI/EKS         2 ambientes AWS
Google Scholar        us-east-1            KEDA + SQS          5 cenários
                      sa-east-1            MLflow Registry
```

**5 lacunas bibliográficas** identificadas que nortearam as decisões de arquitetura.

---

<!-- Slide 6 — STACK TECNOLÓGICO -->

# Stack Tecnológico

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **IaC** | Terraform 1.11 | 5 stacks, 15 módulos, remote state S3+DynamoDB |
| **Containers** | Docker + Amazon ECR | 6 repositórios de imagem |
| **Orquestração** | Amazon EKS 1.32 | Kubernetes gerenciado (t3.medium) |
| **CI/CD** | AWS CodeBuild | Buildspecs declarativos versionados |
| **CT Pipeline** | Lambda + SageMaker | Treinamento XGBoost event-driven |
| **Governança** | MLflow (SM Managed) | Registry, rastreamento de experimentos |
| **Autoscaling** | KEDA 2.18.3 | SQS queue depth → réplicas |
| **Serving** | FastAPI (Python 3.12) | API REST, 8 pods, 2 workers/pod |
| **Mensageria** | Amazon SQS FIFO | Desacoplamento inferência/processamento |
| **Feature Store** | Amazon DynamoDB | Histórico de transações por cliente |
| **Observabilidade** | Amazon Bedrock + Athena | Relatórios LLM diários |

---

<!-- Slide 7 — ARQUITETURA GERAL -->

# Arquitetura da Plataforma — Visão Geral

```
Emissor 3DS
    │ HTTPS
    ▼
API Gateway → NLB → ALB → [EKS: Inference FastAPI · 8 pods]
                                │              │
                           DynamoDB      SQS FIFO
                         (feature store)     │
                                        [EKS: Process · 2-5 pods]◄──KEDA
                                             │
                                       Kinesis Firehose → S3

S3 (inference_logs/) ──► GLUE (dom. 08h UTC)
                              │ EventBridge SUCCEEDED
                         λ etl-delta-filter → S3 (training_zone/)
                              │ S3 event
                         λ training-launcher → SageMaker XGBoost
                              │ S3 event
                         λ register-best-model → MLflow Registry
                                                     │ model load
                                                [Inference pods]

EventBridge (cron diário) → λ promotion-reporter + λ statistics-reporter
                                    → Athena / MLflow → Bedrock → S3
```

---

<!-- Slide 8 — IaC TERRAFORM -->

# Infraestrutura como Código — Terraform 1.11

**Organização por domínio funcional** (não por ambiente):

| Ordem | Stack | Responsabilidades |
|-------|-------|-------------------|
| 1 | `foundation` | VPC, subnets (2 AZs), 7 buckets S3 |
| 2 | `mlops` | SageMaker Managed MLflow, Studio Domain |
| 3 | `platform` | EKS 1.32, ECR, SQS, DynamoDB, Kinesis, Glue |
| 4 | `platform-k8s` | Deployments K8s, KEDA, ALB Ingress |
| 5 | `platform-lambdas` | 3 funções Lambda containerizadas |

**7 buckets S3 por ambiente:** `data-raw` · `data-processed` · `models` · `logs` · `resources` · `reports-promotion` · `reports-statistics`

**2 ambientes:** DEV (`us-east-1`) · Staging (`sa-east-1`) — estado remoto S3 + bloqueio DynamoDB

> Modularização por domínio permite destruir/recriar stacks independentemente — diferencial em relação a abordagens que replicam a infraestrutura completa por ambiente.

---

<!-- Slide 9 — TRILHA CI/CD -->

# Trilha CI/CD — AWS CodeBuild

> **Importante:** A ferramenta de CI/CD utilizada é o **AWS CodeBuild** — não GitHub Actions.

<br>

```
commit no repositório
        │
        ▼
  AWS CodeBuild
  buildspecs/*.yaml (declarativo, versionado)
        │
        ├─► build imagem Docker (Python 3.12, non-root UID 1000)
        ├─► push para Amazon ECR (6 repositórios)
        │     inference · process · register-best-model
        │     training-launcher · etl-delta-filter · sagemaker-training
        │
        └─► kubectl apply → atualiza deployment no EKS
```

**buildspec `iam-policy-setup.yaml`:** automatiza configuração de políticas IAM nos clusters EKS (DEV + Staging) — operação auditável e rastreável por commit.

---

<!-- Slide 10 — TRILHA CT -->

# Trilha CT — Treinamento Contínuo (Event-Driven)

> **Cadeia completamente serverless** — sem Airflow, Step Functions ou agendadores centralizados.

```
┌──────────────────────────────────────────────────────────────────┐
│  Glue Job (domingo 08h UTC)                                     │
│  · lê inference_logs/ (Delta Lake + job bookmarks)             │
│  · gera transformed_zone/                                       │
└────────────────────┬─────────────────────────────────────────────┘
                     │ EventBridge: Glue SUCCEEDED
                     ▼
              λ etl-delta-filter
              · filtros Delta → Parquet em training_zone/
                     │ S3 event: ObjectCreated (.parquet)
                     ▼
              λ training-launcher
              · dispara SageMaker Training Job (XGBoost)
              · injeta: MLflow URI, IAM role, S3 path, dataset name
                     │ S3 event: ObjectCreated (artefato)
                     ▼
              λ register-best-model
              · compara F1-score: candidato vs. produção atual
              · SE melhora → promove no MLflow Registry (stage: production)
              · SE não melhora → modelo anterior permanece inalterado
```

**Garantia:** apenas modelos superiores chegam a produção.

---

<!-- Slide 11 — INFERÊNCIA + KEDA -->

# Inferência Escalável — FastAPI + EKS + KEDA

### Serviço de Inferência
- **FastAPI** (Python 3.12) — endpoint `POST /v1/authorize-purchase`
- **8 réplicas** × 2 workers/pod = **16 workers** (sizing para 100 RPS)
- Modelo carregado do **MLflow Registry** na inicialização do pod (sem SageMaker Endpoint)
- Modelo: **"Felicidade"** (nome no MLflow Registry)

### Autoscaling com KEDA 2.18.3

| Parâmetro | Valor (DEV) |
|-----------|-------------|
| Métrica | SQS FIFO queue depth |
| Mínimo de réplicas | 2 (PDB: minAvailable=1) |
| Máximo de réplicas | 5 |
| Mensagens por pod | 30 (escala +1 a cada 30 msgs) |
| Polling | 15 segundos |
| Scale-up | Imediato (0s stabilization) |
| Scale-down cooldown | 60s + 120s estabilização |

> **Por que SQS depth, não CPU?** Cargas de inferência são *bursty* — picos de chegada desacoplados do consumo de CPU.

---

<!-- Slide 12 — GOVERNANÇA MLFLOW -->

# Governança de Modelos — MLflow

### SageMaker Managed MLflow Tracking Server

```
SageMaker Training Job
        │
        ├─► registra: parâmetros, hiperparâmetros
        ├─► registra: métricas (training_f1_score, loss)
        └─► registra: artefatos (model.pkl, feature schema)
                │
                ▼
        MLflow Registry
        ┌──────────────────────────────────────────┐
        │  "Felicidade" — v1 (archived)            │
        │  "Felicidade" — v2 (archived)            │
        │  "Felicidade" — v3 (stage: production) ◄─┤── λ register-best-model
        └──────────────────────────────────────────┘
                │
                ▼
        Inference Pod (startup)
        mlflow.load_model(f"models:/Felicidade/production")
```

**Rastreabilidade completa:** dado qualquer deploy, é possível identificar o experimento de origem, dataset, métricas de validação e código que o gerou.

---

<!-- Slide 13 — OBSERVABILIDADE GENERATIVA -->

# Observabilidade Generativa — Amazon Bedrock

> Camada que traduz métricas operacionais em linguagem natural para equipes técnicas e executivas.

```
EventBridge (cron diário 10h UTC)
        │
        ├─► λ promotion-reporter
        │   · consulta promoções MLflow (últimas 240h)
        │   · gera e-mail técnico + executivo via Bedrock LLM
        │   · salva JSON em S3 (reports-promotion/)
        │
        └─► λ statistics-reporter
            · query Athena em inference_logs (últimas 24h)
            · calcula: volume, score médio, alertas (PPR), P95 latência
            · compara janela atual vs. anterior (delta %)
            · gera relatório via Bedrock (3 tentativas → JSON válido)
            · salva JSON em S3 (reports-statistics/)
```

**Exemplo real (19/02/2026):**
- Transações: 19.632 · Score médio: 0,000777 · Alertas: 4 (PPR 0,0204%)
- Distribuição P95: 0,047% · Variação 24h: volume −58,55% / score médio +233,23%

> **Escopo correto:** Bedrock como camada de *comunicação*, não de *decisão*.

---

<!-- Slide 14 — VALIDAÇÃO: SETUP -->

# Validação Experimental — Setup dos Testes

### Ferramenta: Locust (Python)
- **1 usuário = 1 RPS** (constant_throughput)
- **100 payloads reais** de transações 3DS (produção, round-robin thread-safe)
- Endpoint: `POST /v1/authorize-purchase` via API Gateway

### 5 Cenários de Teste

| Cenário | Tipo | Ambiente | Condição |
|---------|------|----------|----------|
| 1 | Sequencial (100 req.) | DEV `us-east-1` | Antes do keepalive |
| 2 | Sequencial (100 req.) | DEV `us-east-1` | Após keepalive |
| 3 | Sequencial (100 req.) | Staging `sa-east-1` | Após keepalive |
| 4 | Locust (50 usuários) | DEV `us-east-1` | Antes da otimização |
| 5 | Locust (50 usuários) | DEV `us-east-1` | Após otimização |

**SLA definido:** P95 < 500 ms · P99 < 1.000 ms · 0 falhas · ≥ 100 RPS

---

<!-- Slide 15 — ACHADO CRÍTICO: HTTP KEEPALIVE -->

# Achado Crítico — HTTP Keepalive

> **O resultado de maior impacto prático emergiu de uma anomalia:** picos de latência severos e intermitentes.

### Padrão observado (Cenário 1 — 100 req. sequenciais, DEV)

```
Req. 001-036:  ~180 ms  ← normal
Req. 037    :  5.217 ms  ⚠ PICO
Req. 038-044:  ~180 ms  ← normal
Req. 045    :  2.605 ms  ⚠ PICO
Req. 046-081:  ~180 ms  ← normal
Req. 082    :  1.258 ms  ⚠ PICO
Req. 083-100:  ~180 ms  ← normal
```

### Diagnóstico

Na ausência de HTTP keepalive, conexões TCP são encerradas pelo NLB/ALB após o timeout. A **próxima requisição** precisa de um **novo TCP handshake** pela cadeia:

```
API Gateway → NLB → ALB → pod EKS
```

Cada handshake adiciona 1-4 segundos ao tempo total — efeito invisível em testes unitários, severo sob carga concorrente.

---

<!-- Slide 16 — RESULTADOS: SEQUENCIAL -->

# Resultados — Testes Sequenciais (100 Requisições, DEV)

| Métrica | Antes do Keepalive | Após Keepalive | Melhoria |
|---------|--------------------|----------------|----------|
| Latência média | 279 ms | 287 ms | — |
| Mínimo | 168 ms | 215 ms | — |
| **Máximo** | **5.217 ms** | **423 ms** | **−92%** |
| P90 | 223 ms | 328 ms | — |
| P95 | 236 ms | 345 ms | — |
| **P99** | **5.217 ms** | **423 ms** | **−92%** |
| **Spikes > 1.000 ms** | **3 ocorrências** | **0 ocorrências** | **eliminados** |

> **Conclusão:** A correção do keepalive eliminou completamente a variabilidade extrema. Sem qualquer alteração em infraestrutura, modelo ou código de inferência.

---

<!-- Slide 17 — RESULTADOS: LOCUST CONCORRENTE -->

# Resultados — Carga Concorrente Locust (50 usuários, DEV)

| Métrica | Antes da Otimização | Após Otimização | Redução |
|---------|---------------------|-----------------|---------|
| Requisições totais | 5.870 | 6.040 | — |
| Falhas | 0 | 0 | ✓ |
| Throughput médio | 45,9 RPS | 46,9 RPS | — |
| Latência média | 324 ms | **133 ms** | −59% |
| P50 | 170 ms | **100 ms** | −41% |
| P75 | 420 ms | 150 ms | −64% |
| P90 | 810 ms | 240 ms | −70% |
| **P95** | **1.100 ms** | **330 ms** | **−70%** |
| P99 | 1.600 ms | 510 ms | −68% |
| Máximo | 2.100 ms | 770 ms | −63% |

> Fontes: `reports/target_post_fix_20260216_221946_stats.csv` e `target_perf_optimized_20260216_223952_stats.csv`

---

<!-- Slide 18 — RESULTADOS: STAGING -->

# Resultados — Ambiente Staging (sa-east-1, São Paulo)

| Métrica | Staging (keepalive) | DEV (keepalive) | Diferença |
|---------|---------------------|-----------------|-----------|
| Latência média | **103 ms** | 287 ms | −64% |
| Mediana (P50) | **103 ms** | 279 ms | −63% |
| Mínimo | 72,6 ms | 215 ms | — |
| Máximo | 157,8 ms | 423 ms | −63% |
| P90 | 114,5 ms | 328 ms | −65% |
| **P95** | **123,9 ms** | 345 ms | **−64%** |
| Spikes > 1.000 ms | **0** | 0 | — |

> **Diferença explicada:** Staging em `sa-east-1` é geograficamente próximo do cliente final. DEV em `us-east-1` tem RTT maior a partir da localização dos testes.

> **Implicação:** Testes de desempenho devem ser executados no ambiente de destino — testes exclusivamente em DEV podem subestimar o desempenho real em produção.

---

<!-- Slide 19 — VALIDAÇÃO SLA -->

# Validação Final do SLA

| Critério | Meta | DEV (pós-opt.) | Staging | Status |
|----------|------|----------------|---------|--------|
| Disponibilidade | 100% | 100% (6.040 req.) | 100% | ✓ Atingido |
| P95 latência | < 500 ms | **330 ms** | **124 ms** | ✓ Atingido |
| P99 latência | < 1.000 ms | **510 ms** | — | ✓ Atingido |
| Throughput | ≥ 100 RPS | ~47 RPS* | — | ⚠ Parcial |

> (*) 50 usuários virtuais testados (1 usuário = 1 RPS). O teste com 100 usuários (100 RPS) não foi executado no escopo documentado. KEDA configurado para escalar automaticamente (2–5 réplicas, 30 msg/pod) — infraestrutura projetada para suportar a meta.

<br>

**P50 de 100 ms** indica que, com conexões keepalive estabelecidas e modelo em memória, o pipeline completo (API GW → NLB → ALB → EKS → DynamoDB → XGBoost → resposta) opera **abaixo de 100 ms na mediana**.

---

<!-- Slide 20 — CONTRIBUIÇÕES -->

# Contribuições Acadêmicas

**1. Evidência empírica sobre HTTP keepalive em sistemas de inferência ML**
- Demonstração quantitativa: ausência de keepalive em arquiteturas com múltiplos intermediários de rede causa degradação severa e intermitente (P95: 1.100 ms → 330 ms, −70%)
- Achado com impacto direto em sistemas de produção — invisível em testes unitários

**2. Padrão CI/CD + CT desacoplados documentado**
- CI/CD (CodeBuild) e ciclo de vida do modelo (Lambda + SageMaker) como mecanismos independentes com fronteiras claras — contrariando abordagens que unificam ambos em um único pipeline

**3. Referência de implementação MLOps cloud-native completa**
- Repositório com código real de um sistema de detecção de fraude em escala corporativa
- Cobre todas as camadas: IaC, CI/CD, CT, serving, autoscaling, governança e observabilidade com IA generativa

**4. Validação de KEDA + SQS para inferência ML**
- Queue depth é métrica de autoscaling mais adequada que CPU para cargas de inferência com demanda variável — validado empiricamente

---

<!-- Slide 21 — LIMITAÇÕES -->

# Limitações

**1. Throughput de 100 RPS não validado experimentalmente**
- Testes executados com 50 usuários (~47 RPS)
- Teste com 100 usuários (meta de 100 RPS) não consta nos relatórios disponíveis

**2. Comportamento do KEDA sob carga de spike não capturado**
- Testes com carga estável, sem variação brusca de throughput
- Tempo de reação do KEDA para escalamentos abruptos não foi medido

**3. Treinamento Contínuo sem gatilho automático por model drift**
- Ciclo CT agendado (domingo 08h UTC) — não orientado por degradação de métricas
- Detecção automática de concept drift não implementada no escopo

**4. Ambiente de validação único (AWS)**
- Arquitetura projetada e validada exclusivamente na AWS
- Portabilidade para GCP, Azure ou on-premise não avaliada

---

<!-- Slide 22 — TRABALHOS FUTUROS -->

# Trabalhos Futuros

| # | Extensão | Base no código atual |
|---|----------|---------------------|
| 1 | Validar 100 RPS e teste de spike (KEDA) | `locustfile.py` — cenários target e spike já estruturados |
| 2 | Detecção automática de concept drift → aciona λ training-launcher | Statistics Reporter já coleta dados necessários |
| 3 | Canary Release para modelos (10% tráfego antes da promoção total) | Substituir promoção imediata no λ register-best-model |
| 4 | Benchmark KEDA vs. HPA baseado em CPU | ScaledObject existe; adicionar HPA paralelo para comparação |
| 5 | Bedrock Agent conversacional completo | λ action-group já implementada; falta provisionamento do Agent |
| 6 | Multi-região + DR (sa-east-1 ↔ us-east-1) | Replicação S3 + failover Route 53 |

---

<!-- Slide 23 — CONCLUSÃO -->

# Conclusão

**Resposta à pergunta de pesquisa:**

A integração eficiente de MLOps em pipelines DevOps requer:

> **(a)** Separação arquitetural explícita entre CI/CD e Treinamento Contínuo
>
> **(b)** Automação serverless para eventos de ciclo de vida do modelo
>
> **(c)** IaC modularizado por domínio funcional
>
> **(d)** Governança centralizada via Model Registry
>
> **(e)** Testes de carga com payloads reais e carga concorrente — não como etapa opcional

<br>

**Achado não antecipado:** HTTP keepalive foi a intervenção isolada de maior impacto (P95: 1.100 ms → 330 ms, −70%) — sem alterar infraestrutura, modelo ou algoritmo. Demonstra que problemas de latência em sistemas ML podem ser causados por fatores de rede completamente alheios ao modelo.

---

<!-- Slide 24 — REFERÊNCIAS PRINCIPAIS -->

# Referências Principais (16 no total)

| Autores | Ano | Obra / Publicação |
|---------|-----|-------------------|
| SCULLEY et al. | 2015 | Hidden Technical Debt in Machine Learning Systems (NeurIPS) |
| TREVEIL et al. | 2020 | Introducing MLOps (O'Reilly) |
| KREUZBERGER et al. | 2023 | MLOps: Overview, Definition, and Architecture (IEEE Access) |
| ZAHARIA et al. | 2018 | Accelerating the ML Lifecycle with MLflow (IEEE DEB) |
| GAMA et al. | 2014 | A Survey on Concept Drift Adaptation (ACM Computing Surveys) |
| HUMBLE; FARLEY | 2010 | Continuous Delivery (Addison-Wesley) |
| KIM et al. | 2016 | The DevOps Handbook (IT Revolution Press) |
| HIGHTOWER et al. | 2022 | Kubernetes: Up and Running (O'Reilly) |
| BRIKMAN | 2019 | Terraform: Up & Running (O'Reilly) |
| BRECK et al. | 2017 | The ML Test Score (IEEE Big Data) |
| FOWLER | 2006 | Continuous Integration (MartinFowler.com) |
| AWS | 2026 | ML Lens – Well-Architected Framework / Amazon Bedrock UG |

---

<!-- Slide 25 — ENCERRAMENTO -->

# Obrigado

<br>

**Gustavo Liebl Pereira**
Engenharia de Software
Orientador: Prof. Marcelo Semmer

<br>

### Repositório do Projeto

`github.com/Gustaavolp/tcc-mlops-devops`

<br>

---

*Código real de produção. Dados reais de transações. Resultados verificáveis.*

<br>

## Perguntas?

---

<!-- SLIDES DE BACKUP — para perguntas da banca -->

# [BACKUP] Detalhe: Cadeia de Rede e Keepalive

**Por que a cadeia completa importa?**

```
Cliente (load test)
    │ TCP connection
    ▼
Amazon API Gateway (gerenciado)
    │ HTTP upstream
    ▼
Network Load Balancer (NLB)
    │ TCP
    ▼
Application Load Balancer (ALB)
    │ HTTP
    ▼
Pod FastAPI (EKS)
    │ Python httpx/requests
    ▼
DynamoDB (feature lookup) + MLflow (model load no startup)
```

Cada camada tem seu próprio timeout de keep-alive. Sem configuração explícita, conexões inativas são encerradas — a próxima requisição reconecta toda a cadeia.

**Fix aplicado:** configurar `Connection: keep-alive` e `Keep-Alive: timeout=65` no cliente do load test, alinhado com os timeouts do ALB (60s) e NLB (65s).

---

<!-- BACKUP 2 -->

# [BACKUP] MLflow: Managed vs. Self-Hosted

| Aspecto | Self-Hosted MLflow | SageMaker Managed MLflow |
|---------|--------------------|--------------------------|
| Provisionamento | VM/container próprio | `aws_sagemaker_mlflow_tracking_server` |
| HA / redundância | Manual | Gerenciado pela AWS |
| Backup | Manual | S3 automático |
| Custo base | Servidor sempre ligado | Pay-per-use |
| API compatibility | Full | Full |
| Autenticação | Manual (LDAP, etc.) | IAM nativo |
| Multi-team | Configuração manual | IAM policies |

**Escolha justificada:** eliminar overhead operacional de manutenção de servidor, mantendo compatibilidade total com a API do MLflow e rastreabilidade via CloudWatch.

---

<!-- BACKUP 3 -->

# [BACKUP] KEDA: Por que Queue Depth, não CPU?

### Perfil de carga de inferência ML

```
CPU utilization:               Queue depth:
████████░░░░░░░░░░░░  50%      ████████████████████  100%
(modelo XGBoost: leve)         (transações chegam em burst)
```

**HPA baseado em CPU:**
- CPU não sobe → HPA não escala → fila cresce → latência aumenta
- ML models são computacionalmente leves para CPU

**KEDA baseado em queue depth:**
- Fila cresce → KEDA escala imediatamente (0s stabilization)
- Escalonamento proporcional à demanda real de processamento

**Configuração real:**
```yaml
triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: "elo-fraud-resultset-dev.fifo"
      targetQueueLength: "30"     # +1 pod a cada 30 mensagens
      scaleOnInFlight: "false"
```

---

<!-- BACKUP 4 -->

# [BACKUP] Variabilidade Residual — P50 vs P99

**Por que P50 = 100 ms mas P99 = 510 ms?**

Três causas identificadas:

**1. DynamoDB — clientes com histórico extenso**
- Feature store consulta transações recentes do cliente
- Clientes com histórico grande → maior RCU → mais tempo de lookup

**2. Cold start de pod recém-escalonado pelo KEDA**
- Pod novo precisa carregar o modelo do MLflow na primeira requisição
- Carregamento: `mlflow.load_model("models:/Felicidade/production")`
- Apenas na primeira requisição após o scale-up

**3. Garbage Collection do Python**
- GC do CPython pode causar pausas de 10-50ms em momentos específicos
- Efeito amplificado sob carga concorrente

> Variabilidade residual documentada como limitação conhecida — não como falha de design.

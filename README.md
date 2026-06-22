# Elo | Evolução Compra Online — Predição de Fraude

**TCC:** Integração de MLOps em Pipelines DevOps: Desafios e Boas Práticas para Entrega Contínua de Modelos de Machine Learning em Produção  
**Autor:** Gustavo Liebl Pereira | **Orientador:** Prof. Marcelo Semmer | **Curso:** Engenharia de Software — Mafra, SC | **Ano:** 2026

Este repositório contém o projeto técnico de **detecção de fraude em transações de compra online** (protocolo 3DS), desenvolvido em ambiente de produção na AWS, utilizado como estudo de caso do TCC.

---

## Para Começar

**Novo no projeto?** Siga estes passos:

1. **Leia primeiro**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Guia completo de setup e desenvolvimento
2. **Entenda a estratégia**: [BUILD_STRATEGY.md](BUILD_STRATEGY.md) - Plano de 60 dias em 4 sprints
3. **Visão da arquitetura**: [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) - Arquitetura completa e fluxos de dados

### Quick Start
```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências
make install-dev

# 3. Configurar variáveis de ambiente
cp .env.example .env

# 4. Verificar se tudo está ok
make format && make lint && make test
```

### Terraform Setup
```bash
# Com tfenv:
tfenv install 1.11.0
tfenv use 1.11.0

# Inicializar e validar
cd infra/environments/dev
terraform init
terraform validate
```

---

## Arquitetura da Solução

A arquitetura foi desenhada para ser escalável, resiliente e observável, utilizando os seguintes componentes na AWS:

- **Entrada Síncrona (Real-time Scoring)**
  - **API Gateway (REST)**: Recebe as requisições de transação via endpoint `/v1/authorize-purchase`.
  - **Amazon EKS — inference (FastAPI)**: Serviço de inferência que enriquece os dados e retorna o score de fraude; autoscaling orientado a eventos via KEDA.
  - **Amazon DynamoDB**: Armazena o histórico recente de transações para enriquecimento em tempo real.
  - **MLflow (SageMaker Managed Tracking)**: Versiona e serve o modelo XGBoost; a inferência carrega o modelo diretamente via MLflow, sem SageMaker Endpoint.

- **Ingestão & Histórico (Near Real-time)**
  - **Amazon SQS (FIFO)**: Garante o processamento ordenado e assíncrono dos resultados das transações.
  - **Amazon EKS — process (worker)**: Processa os itens da fila, atualizando o histórico de longo prazo e o banco de dados de tempo real.
  - **Amazon S3**: Armazena o histórico completo de transações para análises e retreino do modelo.

- **Analytics & Business Intelligence**
  - **Amazon Athena & Amazon QuickSight**: Utilizados para criar dashboards executivos e operacionais a partir dos dados armazenados no S3.

- **Explicabilidade & GenAI (Off-path)**
  - **Amazon Bedrock**: Agente de análise em linguagem natural sobre métricas de fraude e promoção de modelos.

- **Observabilidade**
  - **Amazon CloudWatch**: Centraliza métricas, alarmes e logs estruturados, garantindo rastreabilidade ponta a ponta com um `trace_id`.

- **CI/CD & Infraestrutura como Código (IaC)**
  - **Terraform 1.11**: Gerencia toda a infraestrutura AWS (15 módulos, 5 stacks de ambiente).
  - **AWS CodeBuild**: Pipelines de CI/CD para automação operacional. O buildspec em [`buildspecs/iam-policy-setup.yaml`](buildspecs/iam-policy-setup.yaml) automatiza cleanup de IAM resources órfãos e configuração de policies nas roles EKS (DEV e STAGING).

---

## Estrutura do Repositório

```
/
├── docs/tcc/               ← Documentos acadêmicos do TCC
├── infra/                  ← IaC: Terraform (15 módulos, 5 stacks AWS)
│   ├── modules/            ← Módulos reutilizáveis (eks, mlflow, keda, bedrock-agent…)
│   └── environments/
│       └── dev/            ← Stacks: foundation, mlops, platform, platform-k8s, platform-lambdas
├── services/
│   ├── inference/          ← FastAPI: enriquece payload, carrega modelo via MLflow, publica SQS
│   └── process/            ← Worker EKS: consome SQS e grava em S3/DynamoDB
├── lambdas/
│   ├── register-best-model/   ← Promoção automática do melhor modelo no MLflow Registry
│   ├── training-launcher/     ← Dispara jobs de treino no SageMaker
│   └── etl-delta-filter/      ← Filtra delta de dados para retreino
├── models/
│   ├── src/                   ← Treinamento local/interativo (XGBoost + MLflow localhost)
│   └── sagemaker_training/    ← Job de treino em produção (S3 Parquet, CLI args, SMOTEENN)
├── agent_bedrock/          ← Agente AWS Bedrock: análise de métricas de fraude via GenAI
├── k8s/
│   └── dev/                ← Manifestos Kubernetes: deployments, KEDA ScaledObject, HPA, PDB
├── buildspecs/
│   └── iam-policy-setup.yaml  ← CodeBuild: limpeza de IAM órfãos + setup de policies EKS
├── glue/                   ← Jobs AWS Glue para ETL e feature engineering
├── preprocessing/          ← Módulo de pré-processamento e enriquecimento de dados
├── schemas/                ← JSON Schemas e contrato OpenAPI da API
├── notebooks/              ← Análise Exploratória de Dados (EDA) e baselines
├── bases_de_dados/         ← Dataset sintético (150 campos, protocolo 3DS)
├── load-tests/             ← Testes de carga Locust (~100 RPS, p50 ~630ms, 0% erros)
├── docs/                   ← Documentação técnica, diagramas e arquitetura histórica
├── scripts/                ← Scripts utilitários
├── src/                    ← Módulos compartilhados
├── BUILD_STRATEGY.md       ← Plano de desenvolvimento (4 sprints, 60 dias)
├── Makefile                ← Atalhos de desenvolvimento
├── pyproject.toml          ← Configuração de ferramentas Python
└── requirements.txt        ← Dependências de produção
```

---

## Guia de Navegação para o Avaliador do TCC

Os documentos acadêmicos estão em [`docs/tcc/`](./docs/tcc/).

### Objetivo 2 — Infraestrutura como Código (IaC)

| O que ver | Caminho |
|-----------|---------|
| Catálogo dos 15 módulos Terraform | [`infra/modules/README.md`](./infra/modules/README.md) |
| Stack foundation (VPC, S3) | [`infra/environments/dev/foundation/`](./infra/environments/dev/foundation/) |
| Stack mlops (MLflow, SageMaker Studio) | [`infra/environments/dev/mlops/`](./infra/environments/dev/mlops/) |
| Stack platform (EKS) | [`infra/environments/dev/platform/`](./infra/environments/dev/platform/) |
| Stack platform-k8s (KEDA, ALB Controller) | [`infra/environments/dev/platform-k8s/`](./infra/environments/dev/platform-k8s/) |
| Stack platform-lambdas | [`infra/environments/dev/platform-lambdas/`](./infra/environments/dev/platform-lambdas/) |
| Documentação IaC completa | [`infra/README.md`](./infra/README.md) |

### Objetivo 3 — Pipeline CI/CD

| O que ver | Caminho |
|-----------|---------|
| Buildspec AWS CodeBuild (IAM setup EKS) | [`buildspecs/iam-policy-setup.yaml`](./buildspecs/iam-policy-setup.yaml) |

### Objetivo 4 — Governança e Rastreamento (MLOps)

| O que ver | Caminho |
|-----------|---------|
| Lambda de promoção automática de modelos | [`lambdas/register-best-model/`](./lambdas/register-best-model/) |
| Lambda de disparo de treinamento | [`lambdas/training-launcher/`](./lambdas/training-launcher/) |
| Módulo Terraform do MLflow | [`infra/modules/mlflow/`](./infra/modules/mlflow/) |
| Script de treinamento local | [`models/src/main.py`](./models/src/main.py) |
| Script de treinamento SageMaker | [`models/sagemaker_training/src/train.py`](./models/sagemaker_training/src/train.py) |

### Objetivo 5 — Inferência Escalável com KEDA

| O que ver | Caminho |
|-----------|---------|
| Serviço de inferência FastAPI | [`services/inference/main.py`](./services/inference/main.py) |
| Worker de processamento SQS | [`services/process/main.py`](./services/process/main.py) |
| Configuração KEDA (ScaledObject) | [`k8s/dev/keda/`](./k8s/dev/keda/) |
| Testes de carga e resultados | [`load-tests/`](./load-tests/) |

### Arquitetura e Documentação Técnica

| O que ver | Caminho |
|-----------|---------|
| Visão geral da arquitetura | [`docs/ARCHITECTURE_OVERVIEW.md`](./docs/ARCHITECTURE_OVERVIEW.md) |
| Diagramas visuais (PNG, SVG, drawio) | [`docs/diagrams/`](./docs/diagrams/) |
| Pipeline ML | [`docs/Pipeline ML.md`](./docs/Pipeline%20ML.md) |
| Contrato da API | [`docs/API_CONTRACT_PROPOSAL.md`](./docs/API_CONTRACT_PROPOSAL.md) |

---

## Objetivos de Nível de Serviço (SLOs) e Resultados Medidos

SLOs de referência e resultados obtidos nos testes de carga em staging (~100 RPS, fev/2026):

| Métrica | SLO | Medido (staging) |
|---------|-----|-----------------|
| Latência p50 | ≤ 500ms | ~630ms |
| Latência p95 | ≤ 1000ms | ~1200ms |
| Taxa de erro (5xx) | < 0,1% | 0% |
| Disponibilidade da API | ≥ 99,9% | — |
| DLQ (mensagens perdidas) | < 0,01% | < 0,01% |

> Os resultados de staging incluem overhead de API Gateway + NLB + uvicorn `timeout_keep_alive=380s`. Ver [`load-tests/`](load-tests/) para dados completos.

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| IaC | Terraform 1.11 |
| Orquestração | Amazon EKS 1.32 (Kubernetes) |
| CI/CD | AWS CodeBuild + Amazon ECR |
| MLOps / Rastreamento | MLflow via SageMaker Managed Tracking Server |
| Autoscaling | KEDA v2.18 (orientado a eventos — fila SQS FIFO) |
| API de Inferência | FastAPI + Amazon API Gateway REST + NLB |
| Feature Store | Amazon DynamoDB (4,6 M itens / 16,4 GB) |
| Modelo | XGBoost — classificação binária de fraude |
| IA Generativa | AWS Bedrock — agente analítico de métricas |
| Data Lake | Amazon S3 (7 buckets) + AWS Firehose + AWS Glue |
| Linguagens | Python 3.12, HCL (Terraform) |

---

## Base Sintética para Desenvolvimento

Artefatos sintéticos em `bases_de_dados/sintetica/`:

- `online-purchase.yaml`: contrato OpenAPI 3.1 do payload de inferência fornecido pela Elo.
- `configuracoes_cenarios.yaml`: parametrização das personas, pesos e distribuições usadas na geração.
- `gerar_base_sintetica.py`: script que produz `dataset_sintetico.csv` e `payloads_sinteticos.jsonl` com o rótulo sintético `fraud_label`.
- `validar_payload.py`: checa qualquer arquivo JSONL/CSV contra o schema e regras de negócio básicas.

> Esses dados são apenas para desenvolvimento. Assim que exemplos reais chegarem, atualize as distribuições no YAML e regenere a base.

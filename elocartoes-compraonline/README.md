# Elo | Evolução Compra Online — Predição de Fraude

Este repositório contém o projeto de **Predição de Fraude para Transações de Compra Online**, uma solução desenvolvida para a Elo. O objetivo principal é identificar transações fraudulentas em tempo real, com um Acordo de Nível de Serviço (SLA) de resposta p95 inferior a 500 milissegundos.

---

## 🚀 Para Começar

**Novo no projeto?** Siga estes passos:

1. **Leia primeiro**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Guia completo de setup e desenvolvimento
2. **Entenda a estratégia**: [BUILD_STRATEGY.md](BUILD_STRATEGY.md) - Plano de 60 dias em 4 sprints
3. **Referência rápida**: [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) - Arquitetura e contratos de dados

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
# Versão do Terraform gerenciada por .terraform-version
# Recomendado: usar tfenv ou asdf

# Com tfenv:
tfenv install 1.11.0
tfenv use 1.11.0

# Verificar versão
terraform version  # Deve retornar 1.11.0 (mínimo: 1.10.0)

# Inicializar e validar
cd infra/environments/dev
terraform init
terraform validate
```

📖 **Detalhes completos em [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**

---

## Arquitetura da Solução

A arquitetura foi desenhada para ser escalável, resiliente e observável, utilizando os seguintes componentes na AWS:

- **Entrada Síncrona (Real-time Scoring)**
  - **API Gateway (HTTP)**: Recebe as requisições de transação.
  - **Amazon ECS (inference)**: Orquestra o serviço de inferência, que enriquece os dados da transação com informações de um banco de dados de baixa latência.
  - **Amazon DynamoDB**: Armazena o histórico recente de transações para enriquecimento em tempo real.
  - **Amazon SageMaker Endpoint**: Hospeda o modelo de Machine Learning para realizar a predição de fraude.

- **Ingestão & Histórico (Near Real-time)**
  - **Amazon SQS (FIFO)**: Garante o processamento ordenado e assíncrono dos resultados das transações.
  - **Amazon ECS (process/resultset)**: Processa os itens da fila, atualizando o histórico de longo prazo e o banco de dados de tempo real.
  - **Amazon S3**: Armazena o histórico completo de transações para análises e retreino do modelo.

- **Analytics & Business Intelligence**
  - **Amazon Athena & Amazon QuickSight**: Utilizados para criar dashboards executivos e operacionais a partir dos dados armazenados no S3.

- **Explicabilidade & GenAI (Off-path)**
  - **Amazon Bedrock**: Usado para gerar explicações em linguagem natural sobre as decisões do modelo e para auxiliar na descoberta de novas features.

- **Observabilidade**
  - **Amazon CloudWatch**: Centraliza métricas, alarmes e logs estruturados, garantindo rastreabilidade ponta a ponta com um `trace_id`.

- **CI/CD & Infraestrutura como Código (IaC)**
  - **Terraform/CloudFormation**: Gerencia a infraestrutura de forma automatizada.
  - **Pipelines de CI/CD**: Implementam deploy do tipo `canary` ou `blue-green` com rollback automático baseado em SLOs.

---

## Estrutura do Repositório

O repositório está organizado da seguinte forma para separar as responsabilidades e facilitar a manutenção:

```
/
├── infra/         # Código de Infraestrutura como Código (Terraform/CloudFormation)
├── services/
│   ├── process/   # Worker ECS que consome da SQS e grava em S3/DynamoDB
│   ├── inference/ # Serviço ECS da API que featuriza e chama o SageMaker
│   └── model/     # Código de treino/inferência e pacote do modelo SageMaker
├── mlops/
│   ├── pipeline/  # Definição dos SageMaker Pipelines (dados→treino→avaliar→deploy)
│   └── monitoring/# Scripts de monitoramento de drift de modelo e performance
├── schemas/       # Contratos de dados (JSON Schema / OpenAPI)
├── notebooks/     # Notebooks para Análise Exploratória de Dados (EDA) e baselines
├── scripts/       # Scripts de utilidades e testes (e.g., smoke, carga)
├── bases_de_dados/# Dados sintéticos e dumps controlados
└── docs/          # Documentação geral, Model Card, dicionário de dados, etc.
```

---

## Objetivos de Nível de Serviço (SLOs)

O serviço foi projetado para atender aos seguintes SLOs:

- **Latência de Scoring**:
  - `p50 ≤ 150ms`
  - `p95 ≤ 500ms`
  - `p99 ≤ 800ms`
- **Disponibilidade da API**: `≥ 99,9%`
- **Taxa de Erro**: `5xx ≤ orçamento definido` | `DLQ < 0,01%`

---

## Base sintética para desenvolvimento

Enquanto aguardamos os dados reais, mantemos um conjunto de artefatos sintéticos em `bases_de_dados/sintetica/`:

- `online-purchase.yaml`: contrato OpenAPI 3.1 do payload de inferência fornecido pela Elo.
- `configuracoes_cenarios.yaml`: parametrização das personas, pesos e distribuições usadas na geração.
- `gerar_base_sintetica.py`: script que, via `.venv`, produz `dataset_sintetico.csv` (tabular) e `payloads_sinteticos.jsonl` (payloads completos) já com o rótulo sintético `fraud_label`.
- `validar_payload.py`: checa qualquer arquivo JSONL/CSV contra o schema e regras de negócio básicas.
- `dicionario_campos.csv`: inventário automatizado de campos/tipos extraído do OpenAPI.

> Esses dados são apenas para desenvolvimento. Assim que exemplos reais chegarem, atualize as distribuições no YAML e regenere a base.

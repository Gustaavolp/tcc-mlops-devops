# Elo | Evolução Compra Online — Build Strategy
*Estratégia completa de construção do projeto de Predição de Fraude*

---

## Visão Geral

Este documento detalha a estratégia de construção do sistema de **Predição de Fraude para Transações de Compra Online** da Elo, organizado em 4 sprints ao longo de 60 dias.

### Objetivo Principal
Implementar uma solução de predição de fraude em tempo real com **SLA p95 < 500ms**, utilizando arquitetura cloud-native na AWS.

---

## Arquitetura Resumida

- **Entrada Síncrona**: API Gateway → ECS (inference) → DynamoDB (últimas X transações) → SageMaker Endpoint
- **Ingestão Assíncrona**: SQS FIFO → ECS (process/resultset) → S3 (history) + DynamoDB
- **Analytics**: Athena + QuickSight para dashboards executivos
- **Explicabilidade**: Bedrock (off-path) para narrativas em linguagem natural
- **MLOps**: Pipeline contínuo com deploy canary/blue-green e auto-rollback
- **Observabilidade**: CloudWatch com rastreamento end-to-end via trace_id

---

## Sprint 1: Foundation & Arquitetura Base (D1–D15)

### Objetivos
Estabelecer a fundação técnica e os contratos de dados do projeto.

### Entregas Principais
1. **Infraestrutura Base (IaC)**
   - Configurar VPC, subnets, security groups
   - Provisionamento de IAM roles e policies
   - Setup inicial de S3 buckets (raw, processed, models)
   - DynamoDB tables (customer_recent_tx)
   - SQS FIFO queue para ingestão

2. **Definições de Negócio**
   - KPIs e métricas de sucesso
   - Objetivos do modelo (precision/recall targets)
   - Dicionário de dados e feature catalog
   - Definição de risk bands e thresholds

3. **Contratos de Dados**
   - `schemas/fraud_scoring_request.schema.json`
   - `schemas/fraud_scoring_response.schema.json`
   - OpenAPI spec para `/v1/score`
   - Versionamento de schemas

4. **Setup de Desenvolvimento**
   - Estrutura de repositório
   - CI/CD pipelines básicos
   - Ambientes (dev, stg, prd)
   - Smoke tests (`scripts/smoke_e2e.sh`)

5. **Baseline Experiment**
   - EDA inicial nos notebooks
   - Modelo baseline simples (regras ou XGBoost)
   - Métricas de performance base

### Tasks Relacionadas
ELOME-37, ELOME-45, ELOME-46, ELOME-40, ELOME-38, ELOME-39, ELOME-47, ELOME-44, ELOME-48

### Critérios de Aceite
- [ ] IaC deployável em ambiente dev
- [ ] Schemas validados e documentados
- [ ] Smoke test executando com sucesso
- [ ] Baseline model com métricas documentadas

---

## Sprint 2: Ingestão Online & ECS Inference (D16–D30)

### Objetivos
Construir os serviços de ingestão e a infraestrutura de featurização.

### Entregas Principais
1. **Serviço de Processamento (`services/process/`)**
   - Worker ECS que consome da SQS FIFO
   - Persistência em S3 (particionado por data/hora)
   - Atualização do DynamoDB (últimas N transações por customer)
   - Tratamento de DLQ e retry logic
   - Dockerfile e deployment via ECS Fargate

2. **Serviço de Inferência (`services/inference/`)**
   - API FastAPI/Flask para scoring
   - Feature engineering on-the-fly
   - Enriquecimento com dados do DynamoDB
   - Client para SageMaker Endpoint
   - Health checks e readiness probes
   - Dockerfile otimizado para latência

3. **Pacote do Modelo (`services/model/`)**
   - Script de treinamento (XGBoost/LightGBM/NN)
   - Inference handler para SageMaker
   - Model serialization (pickle/joblib/ONNX)
   - Unit tests para feature engineering

4. **Dataset de Treino**
   - Pipeline de dados (bronze → silver → gold)
   - Feature store ou S3 versionado
   - Validação de qualidade dos dados
   - Splits estratificados (train/val/test)

5. **MLOps Pipeline Inicial**
   - SageMaker Pipelines (ProcessingStep → TrainingStep → EvaluationStep)
   - Model registry para versionamento
   - Condições de aprovação automática
   - Logs estruturados de experimentos

### Tasks Relacionadas
ELOME-41, ELOME-42, ELOME-51, ELOME-52, ELOME-43, ELOME-53

### Critérios de Aceite
- [ ] SQS → S3 + DynamoDB pipeline funcional
- [ ] API de inferência respondendo < 500ms (p95)
- [ ] Modelo candidato treinado com AUC-PR > baseline
- [ ] Feature importance analisada e documentada
- [ ] Pipeline de MLOps executando end-to-end

---

## Sprint 3: Real-Time Scoring API & Modelo em Produção (D31–D45)

### Objetivos
Integrar todos os componentes e preparar para produção.

### Entregas Principais
1. **Integração API Completa**
   - API Gateway configurado com throttling e WAF
   - Integração ECS Inference ↔ SageMaker Endpoint
   - Caching estratégico (ElastiCache/Redis se necessário)
   - Rate limiting por customer/merchant

2. **Reason Codes & Explicabilidade**
   - SHAP values ou feature contributions
   - Top-N reason codes por transação
   - SDK/biblioteca para integração cliente
   - Documentação de reason codes

3. **Modelo Campeão em Produção**
   - Deploy do modelo com melhor performance
   - Endpoint SageMaker com auto-scaling
   - A/B testing framework (se necessário)
   - Model versioning via headers

4. **Testes de Carga**
   - Scripts k6 ou Locust
   - Simulação de carga realista (TPS esperado)
   - Validação de SLOs sob carga
   - Identificação de bottlenecks

5. **Observabilidade Completa**
   - CloudWatch dashboards (latência, throughput, erros)
   - Alarmes para violação de SLOs
   - Logs estruturados com trace_id
   - Distributed tracing (X-Ray opcional)
   - Métricas customizadas do modelo

### Tasks Relacionadas
ELOME-49, ELOME-50, ELOME-54 (parcial), ELOME-55 (parcial)

### Critérios de Aceite
- [ ] API respondendo com SLOs atendidos
- [ ] Reason codes validados pelo negócio
- [ ] Testes de carga passando (p95 < 500ms)
- [ ] Dashboards operacionais ativos
- [ ] Go/No-Go aprovado para produção

---

## Sprint 4: Validation, Documentation & Handoff (D46–D60)

### Objetivos
Validar a solução em produção, documentar completamente e transferir conhecimento.

### Entregas Principais
1. **Validação em Produção**
   - **Shadow Mode**: Scoring paralelo sem impactar decisões
   - **A/B Testing**: Comparação modelo novo vs. baseline
   - **Canary Deployment**: Ramp-up gradual (5% → 25% → 50% → 100%)
   - **Smoke Tests em Produção**: Validação pós-deploy
   - **Disaster Recovery**: Testes de rollback e failover
   - **Performance Real**: Validação de SLOs com tráfego real

2. **Documentação Técnica**
   - **Model Card**:
     - Métricas de performance (AUC-PR, precision@k, recall@k)
     - Análise de bias e fairness
     - Limitações conhecidas
     - Casos de uso recomendados
   - **API Documentation**:
     - OpenAPI/Swagger completo
     - Exemplos de request/response
     - Error codes e troubleshooting
     - SDK usage guides
   - **Architecture Documentation**:
     - Diagramas de arquitetura (C4 Model)
     - Data flow diagrams
     - Sequence diagrams para fluxos críticos
     - ADRs (Architecture Decision Records)
   - **Data Dictionary**:
     - Catálogo de features com definições
     - Tipos de dados e formatos
     - Regras de negócio aplicadas

3. **Runbooks & Playbooks**
   - **Incident Response**:
     - Playbook para latência alta
     - Playbook para queda de disponibilidade
     - Playbook para drift de modelo
     - Escalation matrix
   - **Operational Runbooks**:
     - Deploy manual step-by-step
     - Rollback procedures
     - Troubleshooting comum
     - Health check procedures
   - **Monitoring Guides**:
     - Interpretação de métricas
     - Alertas e suas ações
     - Dashboard walkthroughs

4. **Knowledge Transfer**
   - **Training Sessions**:
     - Arquitetura overview (DevOps/SRE team)
     - API usage (Integration team)
     - Model monitoring (ML team)
     - Dashboard interpretation (Business/Analytics)
   - **Developer Onboarding**:
     - Setup local environment
     - Contribution guidelines
     - Code review standards
     - Testing requirements
   - **Workshops**:
     - QuickSight dashboard customization
     - MLOps pipeline operation
     - Bedrock explicabilidade usage

5. **Compliance & Governance**
   - **Model Registry**:
     - Versionamento completo
     - Metadata de experimentos
     - Aprovações e auditorias
   - **Data Lineage**:
     - Rastreamento de origem dos dados
     - Transformações aplicadas
     - Controle de acesso
   - **Audit Trail**:
     - Logs de decisões do modelo
     - Rastreabilidade end-to-end
     - Retention policies
   - **LGPD/Privacy Compliance**:
     - Anonimização de dados sensíveis
     - Right to explanation
     - Data deletion procedures

6. **Production Cutover**
   - **Go-Live Checklist**:
     - [ ] Todos os testes passando
     - [ ] Documentação aprovada
     - [ ] Runbooks validados
     - [ ] Team training completo
     - [ ] Backups configurados
     - [ ] Rollback testado
   - **Traffic Ramp-Up Plan**:
     - Dia 1: 10% tráfego + hypercare 24h
     - Dia 2-3: 25% tráfego
     - Dia 4-5: 50% tráfego
     - Dia 6-7: 100% tráfego
   - **Hypercare Monitoring** (72h pós-deploy):
     - War room setup
     - Real-time monitoring
     - Incident response team on-call
   - **Post-Deployment Review**:
     - Lessons learned session
     - Retrospective com stakeholders
     - Improvement backlog

### Tasks Relacionadas
ELOME-54 (completo), ELOME-55 (completo), ELOME-56, tasks de homologação

### Critérios de Aceite
- [ ] Shadow mode validado com sucesso (1+ semana)
- [ ] Model card aprovado por stakeholders
- [ ] Toda documentação técnica completa
- [ ] Runbooks validados em simulações
- [ ] Time operacional treinado e certificado
- [ ] Compliance checklist 100% atendido
- [ ] Go-Live aprovado por todos os stakeholders
- [ ] 72h de hypercare sem incidentes críticos
- [ ] Post-mortem documentado

---

## SLOs & Guardrails

### Service Level Objectives
- **Latência de Scoring**:
  - p50 ≤ 150ms
  - p95 ≤ 500ms (SLA contratual)
  - p99 ≤ 800ms
- **Disponibilidade da API**: ≥ 99,9% (uptime mensal)
- **Taxa de Erro**:
  - 5xx ≤ 0,1% das requisições
  - DLQ < 0,01% das mensagens

### Model Performance Guardrails
- **Drift Detection**:
  - PSI (Population Stability Index) > 0,2 → trigger retreino
  - Queda de AUC-PR > 5% → investigação urgente
- **Data Quality**:
  - Missing values > 10% → alerta
  - Schema validation failure → rejeição

### Operational Guardrails
- **Auto-Scaling**:
  - CPU > 70% → scale out
  - Requests/target > threshold → scale out
- **Auto-Rollback**:
  - p95 > 600ms por 5min → rollback automático
  - Error rate > 1% por 3min → rollback automático

---

## Ferramentas & Stack Técnico

### AWS Services
- **Compute**: ECS Fargate, Lambda (auxiliar)
- **Storage**: S3, DynamoDB
- **ML**: SageMaker (Training, Endpoints, Pipelines)
- **Integration**: API Gateway, SQS FIFO
- **Analytics**: Athena, QuickSight
- **AI**: Bedrock (Claude/Titan)
- **Observability**: CloudWatch, X-Ray (opcional)
- **Security**: IAM, KMS, WAF

### Development Stack
- **Backend**: Python 3.9+ (FastAPI/Flask)
- **ML**: scikit-learn, XGBoost, LightGBM, SHAP
- **IaC**: Terraform ou CloudFormation
- **CI/CD**: GitHub Actions, AWS CodePipeline, ou GitLab CI
- **Testing**: pytest, k6/Locust
- **Containers**: Docker, ECR

### Monitoring & Logging
- **Metrics**: CloudWatch Metrics, Prometheus (opcional)
- **Logs**: CloudWatch Logs (JSON estruturado)
- **Tracing**: X-Ray ou trace_id custom
- **Alerting**: CloudWatch Alarms, SNS

---

## Riscos & Mitigações

### Riscos Técnicos
| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Latência > 500ms | Alto | Média | Caching, otimização de features, modelo mais leve |
| Drift de modelo | Alto | Alta | Monitoramento contínuo, retreino automático |
| DynamoDB hot partitions | Médio | Média | Partition key bem distribuída, auto-scaling |
| SageMaker endpoint down | Alto | Baixa | Fallback para modelo default, multi-AZ |

### Riscos de Projeto
| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Atraso no acesso AWS | Alto | Média | Iniciar processo na semana 1 |
| Dados insuficientes para treino | Alto | Baixa | Validar volume mínimo antecipadamente |
| Mudança de requisitos | Médio | Média | Sprints bem definidas, change control |

---

## Variáveis de Ambiente

### Ambiente de Desenvolvimento
```bash
ENV=dev
ELO_REGION=sa-east-1
SQS_QUEUE_URL=https://sqs.sa-east-1.amazonaws.com/.../elo-fraud-dev
S3_HISTORY_BUCKET=elo-fraud-history-dev
DDB_TABLE_RECENT_TX=customer_recent_tx_dev
SAGEMAKER_ENDPOINT_NAME=elo-fraud-score-dev
API_SCORE_PATH=/v1/score
MODEL_VERSION_HEADER=X-Model-Version
TRACE_HEADER=X-Trace-Id
LOG_LEVEL=DEBUG
```

### Ambiente de Produção
```bash
ENV=prd
ELO_REGION=sa-east-1
SQS_QUEUE_URL=https://sqs.sa-east-1.amazonaws.com/.../elo-fraud-prd
S3_HISTORY_BUCKET=elo-fraud-history-prd
DDB_TABLE_RECENT_TX=customer_recent_tx_prd
SAGEMAKER_ENDPOINT_NAME=elo-fraud-score-prd
KMS_KEY_ID=arn:aws:kms:sa-east-1:...
BEDROCK_MODEL=anthropic.claude-3-sonnet
LOG_LEVEL=INFO
```

---

## Cronograma Visual

```
Dia 1 ━━━━━━━━━━━━━━━ Dia 15 ━━━━━━━━━━━━━━━ Dia 30 ━━━━━━━━━━━━━━━ Dia 45 ━━━━━━━━━━━━━━━ Dia 60
│                       │                       │                       │                       │
│   Sprint 1            │   Sprint 2            │   Sprint 3            │   Sprint 4            │
│   Foundation          │   Ingest & ML         │   Production API      │   Validation & Docs   │
│                       │                       │                       │                       │
├─ IaC Setup            ├─ ECS Services         ├─ API Integration     ├─ Shadow Mode          │
├─ Schemas              ├─ Feature Engineering  ├─ Reason Codes        ├─ Model Card           │
├─ Baseline Model       ├─ Model Training       ├─ Load Testing        ├─ Runbooks             │
├─ Smoke Tests          ├─ MLOps Pipeline       ├─ Observability       ├─ Knowledge Transfer   │
└─ Data Dictionary      └─ Dataset Bronze/Silver└─ Go/No-Go           └─ Production Cutover   │
```

---

## Definição de Pronto (DoD)

### Código
- [ ] Code review aprovado por 2+ pessoas
- [ ] Testes unitários com cobertura > 80%
- [ ] Testes de integração passando
- [ ] Linting e formatação ok (black, flake8, mypy)
- [ ] Sem secrets hardcoded
- [ ] Documentação inline adequada

### Infraestrutura
- [ ] IaC testado em ambiente dev
- [ ] Recursos taggeados corretamente
- [ ] Custo estimado e aprovado
- [ ] Backup/DR configurado
- [ ] Security groups com least privilege

### Modelo ML
- [ ] Métricas > baseline estabelecido
- [ ] Feature importance documentada
- [ ] Bias analysis realizada
- [ ] Model card preenchido
- [ ] Versionamento correto

### Documentação
- [ ] README atualizado
- [ ] API docs gerados
- [ ] Runbook escrito e revisado
- [ ] Diagramas atualizados
- [ ] CHANGELOG atualizado

---

## Contatos & Responsabilidades

### Equipe Core
- **Tech Lead**: [Cristovam Peres] - Arquitetura e decisões técnicas
- **ML Engineer**: [Vinicios] - Modelagem e MLOps
- **AI Engineer**: [Ana Hatsue] - Services e APIs
- **DevOps Engineer**: [Gustavo Liebl] - Infra e CI/CD
- **Data Engineer**: [Bruna] - Pipelines de dados

### Stakeholders
- **Product Owner**: [Tabata Polato] - Priorização e requisitos
- **Business Analyst**: [Alexandre Kuwana] - KPIs e métricas de negócio
- **Security Lead**: [Nome] - Compliance e segurança
- **SRE Lead**: [Denis Santos] - Operação e SLOs

---

## Próximos Passos

### Imediato (Semana 1)
1. Kickoff meeting com todos os stakeholders
2. Solicitar acessos AWS e ferramentas
3. Setup de repositório e CI/CD básico
4. Primeira versão dos schemas
5. Planejamento detalhado da Sprint 1

### Curto Prazo (Sprint 1)
1. Provisionar infraestrutura base
2. Definir KPIs finais com negócio
3. Explorar dados disponíveis (EDA)
4. Treinar modelo baseline
5. Validar viabilidade técnica

### Médio Prazo (Sprint 2-3)
1. Construir serviços core
2. Treinar modelos candidatos
3. Integrar pipeline end-to-end
4. Validar SLOs em staging

### Longo Prazo (Sprint 4+)
1. Deploy produção controlado
2. Monitorar e otimizar
3. Retreino contínuo
4. Evolução de features

---

**Última atualização**: 2025-10-02
**Versão**: 1.0

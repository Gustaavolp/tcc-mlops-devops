# Seção 4 — Metodologia (versão expandida)

Substituição completa da Seção 4 do artigo.  
Corrige: (a) enquadramento "estudo de caso" → projeto real; (b) "GitHub Actions" → AWS CodeBuild; (c) tempo futuro → passado.  
Adiciona: detalhamento técnico real de cada fase com dados verificáveis no repositório.  
Gerado em: 2026-06-22

---

## 4 METODOLOGIA

Este trabalho classifica-se como **pesquisa aplicada de caráter experimental e construtivo**: o pesquisador projetou, implementou e validou experimentalmente uma plataforma de MLOps em um ambiente de produção real, distinto de um estudo de caso observacional. O objeto de pesquisa *é* a própria construção — o sistema implementado constitui tanto o artefato quanto o instrumento de validação. O ambiente de desenvolvimento foi uma empresa de grande porte do setor de pagamentos eletrônicos, com dados reais de transações processados em infraestrutura de nuvem AWS. O trabalho foi estruturado em quatro fases sequenciais, descritas a seguir.

---

### 4.1 Fase 1 — Levantamento Bibliográfico

A pesquisa bibliográfica foi conduzida nas bases IEEE Xplore, ACM Digital Library e Google Scholar, com termos de busca centrados em: *MLOps*, *continuous training*, *model registry*, *infrastructure as code*, *Kubernetes autoscaling* e *concept drift*. O critério de inclusão privilegiou trabalhos que apresentassem implementações práticas ou arquiteturas de referência validadas empiricamente, não apenas taxonomias teóricas.

O levantamento identificou cinco lacunas recorrentes na literatura que nortearam as decisões de arquitetura deste projeto:

1. A maioria das arquiteturas de referência de MLOps apresenta o pipeline de CI/CD e o ciclo de Treinamento Contínuo (CT) como um único fluxo, obscurecendo a separação de responsabilidades entre entrega de código e entrega de modelos (SCULLEY et al., 2015; KREUZBERGER et al., 2023);

2. Poucas implementações documentam o uso de rastreamento de experimentos gerenciado em nuvem (como SageMaker Managed MLflow) em contraste com servidores MLflow auto-hospedados (ZAHARIA et al., 2018);

3. O autoscaling baseado em eventos (KEDA) para cargas de inferência ML é pouco explorado em comparação com abordagens baseadas em CPU (HIGHTOWER; BURNS; BEDA, 2022);

4. O impacto de otimizações de rede (como *HTTP keepalive*) em sistemas de inferência com múltiplas camadas de rede não é sistematicamente documentado;

5. A modularização de IaC (*Infrastructure as Code*) por domínio funcional — não por ambiente — é pouco formalizada para sistemas MLOps (BRIKMAN, 2019; KARIMIBIUKI et al., 2022).

Essas lacunas orientaram as escolhas técnicas das fases seguintes e os critérios de avaliação da fase de validação.

---

### 4.2 Fase 2 — Projeto e Desenvolvimento da Infraestrutura

Toda a infraestrutura foi codificada em **Terraform 1.11**, organizada em **15 módulos reutilizáveis** instanciados por **5 *stacks* independentes** por ambiente. Essa organização — modularização por domínio funcional em lugar de por ambiente — é um diferencial em relação a projetos que replicam a infraestrutura completa por ambiente sem abstrações de módulo.

**Módulos implementados:** `vpc`, `s3`, `eks`, `ecr`, `sqs`, `dynamodb`, `lambda`, `mlflow`, `sagemaker-studio`, `api-gateway`, `nlb`, `firehose`, `glue`, `athena`, `bedrock-agent`.

**Sequência de *stacks*** (dependência explícita via *remote state* em S3 com bloqueio DynamoDB):

| Ordem | Stack | Responsabilidade |
|-------|-------|-----------------|
| 1 | `foundation` | VPC, subnets privadas/públicas (2 AZs), 7 buckets S3 por ambiente |
| 2 | `mlops` | SageMaker Managed MLflow Tracking Server + SageMaker Studio Domain |
| 3 | `platform` | EKS 1.32, ECR, SQS FIFO, DynamoDB, Kinesis Firehose, API Gateway, NLB, Glue, Athena |
| 4 | `platform-k8s` | Deployments Kubernetes, KEDA 2.18.3, AWS Load Balancer Controller, Ingress |
| 5 | `platform-lambdas` | 3 funções Lambda containerizadas (imagens ECR) |

Os 7 buckets S3 provisionados por ambiente são: `data-raw`, `data-processed`, `models`, `logs`, `resources`, `reports-promotion`, `reports-statistics`. Essa separação garante isolamento de responsabilidades no *data lake*.

O estado Terraform de cada *stack* é armazenado em *backend* S3 com bloqueio via DynamoDB, e as *stacks* de camadas superiores consomem os *outputs* das inferiores via `terraform_remote_state`. Esse padrão elimina dependências circulares e permite a destruição e recriação independente de cada camada.

Os dois ambientes implementados são **DEV** (região `us-east-1`, N. Virgínia) e **Staging** (região `sa-east-1`, São Paulo). Cada ambiente é um conjunto independente das 5 *stacks*, com *workspaces* e *tfvars* separados, garantindo paridade de configuração sem compartilhamento de estado.

**Configuração do cluster EKS (DEV):** Kubernetes 1.32, nós `t3.medium` (2 vCPU, 4 GB RAM), grupo de 2 a 4 nós, acesso administrativo via SSO (`kubectl`).

O *MLflow Tracking Server* foi provisionado como serviço gerenciado pelo SageMaker (`aws_sagemaker_mlflow_tracking_server`), eliminando a operação de servidor sem perda de compatibilidade com a API padrão do MLflow. O servidor armazena artefatos de modelo em um bucket S3 dedicado e registra *logs* no CloudWatch.

---

### 4.3 Fase 3 — Implementação dos Pipelines

A fase de implementação produziu três trilhas de automação com responsabilidades distintas e nenhuma dependência de código entre elas.

#### 4.3.1 Trilha CI/CD — AWS CodeBuild

O AWS CodeBuild foi utilizado para automação de infraestrutura operacional. O repositório contém *buildspecs* declarativos versionados em `buildspecs/`, que encapsulam operações de manutenção da infraestrutura AWS em pipelines auditáveis e rastreáveis por *commit*. O *buildspec* `iam-policy-setup.yaml` automatiza a configuração de políticas IAM nos clusters EKS dos ambientes DEV e Staging, garantindo que permissões de acesso a SageMaker, CloudWatch e ECR estejam sempre sincronizadas com o estado declarativo do repositório.

As imagens Docker dos serviços de inferência, processamento e das funções Lambda são versionadas e publicadas no Amazon ECR, com um repositório ECR dedicado por serviço: `inference`, `process`, `register-best-model`, `training-launcher`, `etl-delta-filter` e `sagemaker-training`. O serviço de inferência utiliza Python 3.12 com usuário não-*root* (UID/GID 1000), seguindo boas práticas de segurança em contêineres Kubernetes.

#### 4.3.2 Trilha CT — Treinamento Contínuo (event-driven)

O ciclo de Treinamento Contínuo é implementado como uma **cadeia de eventos serverless**, em que a conclusão bem-sucedida de cada etapa dispara automaticamente a etapa seguinte, sem agendadores centralizados ou orquestradores de *workflow*:

```
Glue Job (agendado) 
  → EventBridge (Glue SUCCEEDED) 
  → Lambda etl-delta-filter (gera Parquet) 
  → S3 event (training_zone/*.parquet) 
  → Lambda training-launcher (dispara SageMaker Job) 
  → S3 event (SageMaker bucket) 
  → Lambda register-best-model (promoção condicional no MLflow)
```

**Etapa 1 — Glue Job** (`job_training_test_1`): agendado semanalmente (domingo, 08h00 UTC), lê *logs* de inferência da `inference_logs/` no bucket `data-processed` e gera a zona transformada (`transformed_zone/`) no formato Delta Lake, aplicando *merge* incremental com *job bookmarks* para processar apenas novos registros.

**Etapa 2 — Lambda `etl-delta-filter`**: acionada via EventBridge quando o Glue Job termina com estado `SUCCEEDED`. Aplica filtros Delta no conjunto transformado e grava arquivos Parquet na `training_zone/`, preparando o *dataset* de treinamento incremental.

**Etapa 3 — Lambda `training-launcher`**: acionada por notificação S3 quando novos arquivos `.parquet` chegam em `training_zone/`. Utiliza o SageMaker ModelTrainer SDK para despachar um *training job* com a imagem de treinamento publicada no ECR. As configurações são injetadas via variáveis de ambiente: URI do MLflow, nome do experimento, IAM role do SageMaker, caminho S3 dos dados e nome do *dataset*.

**Etapa 4 — SageMaker Training Job**: executa o treinamento do modelo XGBoost a partir dos dados Parquet. Parâmetros e métricas (incluindo `training_f1_score`) são registrados automaticamente no MLflow Tracking Server. Ao término, artefatos do modelo são salvos no bucket SageMaker.

**Etapa 5 — Lambda `register-best-model`**: acionada por notificação S3 no bucket SageMaker (`s3:ObjectCreated:*`). Consulta o MLflow, identifica o experimento correspondente ao *job* recém-concluído e compara sua métrica `training_f1_score` com a do modelo atual em produção. Se o novo modelo for superior, promove-o no *MLflow Registry* com a *tag* `stage: production`. Caso contrário, o modelo anterior permanece em produção sem intervenção manual.

Esse mecanismo garante que **apenas modelos melhores que o antecessor chegam a produção**, eliminando o risco de regressão acidental por retreinamento.

#### 4.3.3 Trilha de Inferência — FastAPI + EKS + KEDA

O serviço de inferência é uma API REST implementada com **FastAPI** (Python 3.12), containerizada e implantada no Amazon EKS. O fluxo de rede de uma requisição percorre: API Gateway → NLB (*Network Load Balancer*) → ALB (*Application Load Balancer*) → *pod* EKS.

O modelo é carregado diretamente do **MLflow Registry** na inicialização do *pod*, sem necessidade de *endpoint* SageMaker dedicado. A versão carregada é sempre aquela com *tag* `stage: production` no *registry*, garantindo que o *deploy* de um novo modelo ocorra automaticamente na próxima substituição de *pod*, sem redeploy manual.

O **KEDA 2.18.3** (*Kubernetes Event-driven Autoscaling*) foi instalado via Helm no *namespace* `keda` e configurado com um `ScaledObject` que monitora a profundidade da fila **SQS FIFO** (`elo-fraud-resultset-dev.fifo`) para escalar o serviço de processamento assíncrono (`process`):

| Parâmetro KEDA | Valor DEV |
|----------------|-----------|
| Mínimo de réplicas | 2 (compatível com PDB `minAvailable: 1`) |
| Máximo de réplicas | 5 |
| Mensagens por *pod* | 30 (escala +1 *pod* a cada 30 mensagens) |
| Intervalo de *polling* | 15 segundos |
| *Scale-up* | Imediato (`stabilizationWindowSeconds: 0`) |
| *Scale-down* | Após 60s de *cooldown* + 120s de estabilização |

A escolha da profundidade de fila como métrica de escalonamento — em lugar de CPU — é justificada pelo perfil de carga de inferência: bursty, com picos de chegada de mensagens desacoplados do consumo de CPU dos *pods*.

---

### 4.4 Fase 4 — Validação Experimental

A validação foi realizada com a ferramenta **Locust** (Python), que permite simular usuários virtuais concorrentes com controle preciso de taxa de requisições. A configuração adotada foi **1 usuário = 1 RPS** (*constant\_throughput*), de forma que o número de usuários simultâneos corresponde diretamente ao *throughput* em RPS.

**Corpus de teste:** 100 *payloads* reais de transações 3DS capturados do ambiente de produção, percorridos em sequência *round-robin* com seleção *thread-safe* entre usuários concorrentes. O uso de *payloads* reais — em lugar de dados sintéticos — garante que variações de tamanho, estrutura e conteúdo das transações estejam presentes nos testes, tornando os resultados representativos do tráfego real.

**Critério de sucesso por requisição:** resposta HTTP 200 com campo `score` no *body* JSON. Qualquer desvio — HTTP 4xx, HTTP 5xx, *timeout* ou JSON inválido — é contabilizado como falha.

Foram executados cinco cenários de teste em dois ambientes:

| Cenário | Tipo | Ambiente | Condição |
|---------|------|----------|----------|
| 1 | Sequencial (100 req.) | DEV (`us-east-1`) | Antes da otimização de *keepalive* |
| 2 | Sequencial (100 req.) | DEV (`us-east-1`) | Após otimização de *keepalive* |
| 3 | Sequencial (100 req.) | Staging (`sa-east-1`) | Após otimização de *keepalive* |
| 4 | Locust concorrente (50 usuários) | DEV (`us-east-1`) | Antes da otimização |
| 5 | Locust concorrente (50 usuários) | DEV (`us-east-1`) | Após otimização |

Os cenários sequenciais (1–3) permitiram isolar o comportamento requisição a requisição, revelando anomalias de latência que seriam mascaradas por estatísticas agregadas dos testes de carga. Os cenários Locust (4–5) mediram o desempenho sob carga concorrente real, com coleta de percentis P50, P75, P90, P95, P99, *throughput* médio e taxa de falhas.

Os critérios de aceitação (SLA) definidos para o projeto foram:

| Critério | Meta |
|----------|------|
| Disponibilidade | 100% (0 falhas HTTP) |
| Latência P95 | < 500 ms |
| Latência P99 | < 1.000 ms |
| *Throughput* | ≥ 100 RPS |

Os resultados obtidos e a análise dos dados coletados são apresentados na Seção 7.

---

## Nota de integração no Word

- **Substituição completa:** apagar o texto atual da Seção 4 e substituir por este.
- **Tabelas:** inserir no formato de tabela Word (não como texto pré-formatado).
- **Bloco de código (cadeia CT):** pode ser inserido como caixa de texto monoespaçada ou diagrama de fluxo simplificado.
- **Ajuste de numeração:** se o orientador preferir manter a seção como lista numerada (formato original), o conteúdo das subseções 4.1–4.4 pode ser convertido para itens da lista, mantendo o nível de detalhe.
- **"Estudo de caso" no Resumo/Abstract:** o arquivo `resumo-abstract.md` usa "estudo de caso real" — ver nota abaixo sobre atualização necessária.

---

## Atualização necessária no Resumo/Abstract

O arquivo `resumo-abstract.md` (gerado na Task #20) contém a frase:

> "fundamentada em um estudo de caso real de detecção de fraude em transações de compra *online*"

Deve ser corrigida para:

> "desenvolvida e implantada em ambiente de produção real de uma empresa de grande porte do setor de pagamentos eletrônicos"

A versão em inglês correspondente:

> "grounded in a real-world case study of fraud detection"

Deve ser corrigida para:

> "developed and deployed in a production environment of a large-scale electronic payments company"

Essa correção está alinhada com o enquadramento do trabalho como pesquisa construtiva (não observacional), conforme orientado pelo usuário.

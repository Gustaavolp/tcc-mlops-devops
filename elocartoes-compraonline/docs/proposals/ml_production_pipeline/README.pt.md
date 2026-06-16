# Proposta de Pipeline de ML para Producao

## Objetivo
Orientar a evolucao do fluxo atual baseado em notebooks para um pipeline de ML em producao utilizando servicos AWS (S3, Glue/Athena, SageMaker Processing/Training, Feature Store, Pipelines, Model Registry, Clarify, Model Monitor, Endpoints, CloudWatch).

## Metas
- Assegurar workflows de ML reprodutiveis e auditaveis alinhados aos SLOs de fraude.
- Separar exploracao em notebooks de pipelines automatizados que alimentam producao.
- Padronizar artefatos (datasets, modelos, metricas, aprovacoes) em dev/stg/prd.
- Habilitar ciclos continuos de treino/monitoramento integrados a CI/CD e IaC.

## Arquitetura de Referencia
1. **Base de Dados**
   - Eventos brutos em `S3` (camada bronze), catalogados via `Glue` e consultados com `Athena`.
   - Regras de qualidade (Great Expectations/Deequ) executadas em jobs `SageMaker Processing`.
2. **Engenharia de Features**
   - Transformacoes deterministicas em scripts Python ou exports do Data Wrangler rodando em Processing jobs.
   - Features validadas registradas no `SageMaker Feature Store` (offline e online) com metadata (owner, lineage, PII).
3. **Treino e Avaliacao**
   - `SageMaker Pipelines` orquestrando Processing -> Training -> Evaluation -> gate condicional.
   - Passo de treino usando containers gerenciados (XGBoost, custom) em instancias spot/on-demand.
   - Etapas `Clarify` para bias/drift; metricas no `CloudWatch` e anexadas ao pacote do modelo.
4. **Registry e Deploy**
   - Runs bem-sucedidos registrados no `Model Registry` com dataset version, hiperparametros e metricas.
   - Promocao para staging/producao por aprovacao manual/CI e deploy em `SageMaker Endpoints` (tempo real) ou `Batch Transform`.
   - Camada ECS/API Gateway segue responsavel por orquestracao de requests e SLO.
5. **Monitoramento e Retreino**
   - `Model Monitor` agenda capturas para qualidade de dados, qualidade do modelo, bias e drift; alarmes via CloudWatch.
   - KPIs (AUC-PR, recall em threshold, latencia) em dashboards (CloudWatch, QuickSight, Grafana).
   - Pipelines de retreino acionados por gatilhos de drift ou eventos de negocio.
6. **Governanca & Observabilidade**
   - Jobs emitem logs estruturados com `trace_id` para correlacao ponta a ponta.
   - IaC (Terraform/CDK) codifica infraestrutura, redes, criptografia (KMS) e IAM least privilege.
   - Artefatos versionados em Git com revisao via PR.

## Comparacao: Notebook vs Pipeline
| Aspecto | Somente Notebooks | Pipeline Gerenciado |
|---------|-------------------|---------------------|
| Reproducao | Depende do ambiente do autor | Execucoes deterministicas com rastreabilidade |
| Colaboracao | Dificil revisar/mesclar | Code review, testes, CI/CD |
| Governanca | Trilha limitada | Versionamento, aprovacoes, CloudTrail |
| Automacao | Reexecucao manual | Workflows agendados/gatilhados |
| Controle de Custos | Risco de instancias ociosas | Jobs sob demanda com tags de billing |
| Velocidade Exploratória | Rapida para POC | Iteracao mais lenta, mas modular |

### Workflow Recomendado
1. Usar notebooks/Data Wrangler para exploracao; exportar logica final como scripts (`src/processing/*.py`).
2. Parametrizar scripts via arquivos de configuracao (YAML/JSON) para multiplos datasets/ambientes.
3. Empacotar dependencias em `requirements.txt` ou imagens Docker customizadas.
4. Escrever testes (pytest) para transformacoes e pipelines de treino.
5. Definir `SageMaker Pipeline` em codigo (SDK) e acionar via CI/CD (CodePipeline, GitHub Actions) a cada merge.
6. Registrar artefatos e exigir aprovacao manual antes de producao.
7. Manter notebooks em `notebooks/` apenas para relatórios, apontando para os scripts correspondentes.

## Fases de Implementacao
| Fase | Foco | Entregaveis |
|------|------|-------------|
| P0 | Fundacoes | Estrutura do repo, IaC basica, dataset baseline catalogado |
| P1 | Camada de Processing | Jobs de qualidade de dados, scripts de feature, setup do Feature Store |
| P2 | Pipeline de Treino | Definicao no SageMaker Pipeline, metricas automatizadas, integracao com Model Registry |
| P3 | Automacao de Deploy | CI/CD, provisionamento de endpoints, estrategia canary |
| P4 | Monitoramento | Model Monitor, dashboards, politicas de alerta |
| P5 | Operacao Continua | Gatihos de retreino, dashboards de custo, runbooks |

## Pros e Contras
- **Pros**: reproducibilidade, compliance, reutilizacao de features, deploy automatizado, consistencia de SLA, resposta mais rapida a incidentes.
- **Contras**: investimento inicial maior, necessidade de conhecimentos DevOps/MLOps, pipelines mais rigidos (mudancas exigem review), custos dos servicos gerenciados.

## Pontos em Aberto
- Escolha entre `Step Functions` e `SageMaker Pipelines` para tarefas multi-servico (ex.: acionar ECS).
- Integracao com pipeline CI/CD existente e gestao de segredos (Secrets Manager/Parameter Store).
- Politica de aprovacao no Model Registry (auto x manual, thresholds minimos).
- Estrategia de desenvolvimento local (Docker compose, modo local do SageMaker) para reduzir ciclo de feedback.

## Proximos Passos
- Revisar esta proposta com engenharia, data science e DevOps; registrar decisoes diretamente no documento.
- Identificar notebooks atuais a serem refatorados primeiro e definir owners.
- Esbocar modulos IaC de SageMaker alinhados com `infra/`.
- Definir artefatos minimos de governanca (runbook, RACI, SLAs) antes da virada para producao.

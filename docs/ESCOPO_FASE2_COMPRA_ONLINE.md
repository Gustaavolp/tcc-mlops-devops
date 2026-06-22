# Escopo Fase 2 – Compra Online (Elo)

## Objetivo
Implementar uma solução robusta de detecção de fraudes em transações online, com foco no desenvolvimento, operação e monitoramento do modelo de Machine Learning responsável pelo score de confiabilidade da transação. Com base nos aprendizados adquiridos na fase de MVP, criar um motor preditivo de alta performance, capaz de processar dados transacionais e retornar um score de fraude explicável e confiável.

## Funcionalidades

### Contratos e Integrações (API)
- Padronizar `POST /authorize-purchase` conforme `documentos recebidos/online-purchase.yaml`.
- Validar payloads e estruturar erros (Problem Detail); correlação por ID único/trace.
- Definir versionamento de schema e processo de mudança de contrato.

### Fluxo de Dados 3DS (Síncrono) e TE40 (Assíncrono)
- Síncrono: receber dados 3DS na chamada de inferência.
- Assíncrono: consumir `resultset` (via SQS) com TE40 e marcações de fraude/chargeback.
- Consolidar dicionário de dados, mapeamento 3DS↔TE40 e estratégia de correlação (`NRID`) e idempotência.

### Motor Preditivo de Alta Performance
- Disponibilizar “Score Elo” único e consistente para transações online.
- SLOs de inferência: metas de latência (ex.: p95) e throughput acordados.
- Decisão explicável (reason codes) e política de thresholds; fallback controlado.

### MLOps e Monitoramento do Modelo
- Monitorar performance do modelo (ex.: taxa de FP/FN, estabilidade do score), drift de dados e qualidade de features.
- Alarmes e dashboards para métricas de modelo e de serviço; trilhas de auditoria.
- Processo de tuning/retraining orientado por evidências (dados rotulados e feedback operacional).

### KPIs e Metas (Produto e Operação)
- Fechar North Star + 2–3 KPIs de suporte (a partir dos candidatos nos documentos).
- Instrumentar dashboards e alertas; definir janelas de medição e segmentações (canal/lojista/etc.).
- Incorporar KPIs na priorização de backlog e nos critérios de aceitação.

### Governança, LGPD e Compliance
- Classificar PII e aplicar mascaramento segundo diretrizes de compliance.
- Controles de acesso, retenção, criptografia e auditabilidade; trilha de decisão por transação.

### Observabilidade e Confiabilidade
- Métricas: latências p50/p95/p99, throughput, erros por tipo; tracing distribuído e logs estruturados.
- Idempotência em SQS e correlação ponta-a-ponta; health checks e playbooks de operação.

### Dados de Treinamento e Acesso
- Obter dump histórico (6–12 meses) com labels (chargeback) e metadados (datas de ocorrência/confirmação).
- Formalizar stewards e SLAs de dados (Denis/3DS; Engenharia via Denis/TE40) e catálogo/dicionário.

### CI/CD
- GitHub Actions: testes unitários, contrato e container; deploy para `dev`; testes de carga/infra; promoção para `prod`.
- Política de branches/PRs e gates de qualidade alinhados ao time.

### Implementação de Terraform
- Provisionar via IaC: SQS (resultset), papéis/roles, observabilidade, redes e artefatos do serviço.
- Provisionar recursos de ML e endpoint de inferência conforme arquitetura (ex.: `arquitetura/docs/arquitetura_ml_sagemaker.drawio`).
- Variáveis por ambiente e rotinas de manutenção/destruição com segurança.

## Ajustes relacionados à Fase 1 (MVP)
- Consolidar aprendizados do MVP em requisitos não funcionais (latência, custo, confiabilidade).
- Fechar KPIs (North Star, metas) e incluir no painel executivo.
- Confirmar `NRID` como chave de correlação e regras de unicidade.
- Definir fonte/processo para registrar falsos positivos (owner e sistema).
- Consolidar mapeamento 3DS/TE40 e dicionário de dados.
- Validar requisitos de LGPD/mascaramento e refletir no design técnico.

## Cronograma (4 Sprints + Homologação)
- Sprint 1: Incorporar aprendizados do MVP; KPIs e observabilidade base; revisão do OpenAPI; esqueleto Terraform.
- Sprint 2: Protótipo do serviço de scoring e integração síncrona; consumo inicial de SQS (resultset); testes de contrato.
- Sprint 3: Explicabilidade (reason codes), monitoramento de modelo, tuning inicial, CI/CD completo.
- Sprint 4: Hardening, testes de carga/custos, SLOs, playbooks/runbooks e readiness para produção.
- Homologação: validação end-to-end, critérios de aceite e go-live.

## Entregáveis
- OpenAPI revisado e publicado; testes de contrato cobrindo casos críticos.
- Terraform para `dev` e `prod`; documentação de módulos/variáveis.
- Serviço de inferência operacional com observabilidade e SLOs definidos.
- Pipelines GitHub Actions (build, testes, deploy, carga).
- Dashboards de KPIs e métricas de modelo; playbook/runbook de operações.

## Critérios de Aceite
- Metas de latência/throughput cumpridas no volume alvo acordado.
- KPIs instrumentados e visíveis em dashboards com metas.
- Cobertura de testes de contrato e unitários conforme padrão do time.
- Deploy reprodutível via Terraform/pipeline e rollback testado.
- Coleta de feedback/labels ativa e consultável para tuning/retraining.

## Dependências
- Acesso a bases 3DS e TE40 (histórico e produção), SLAs e dicionário.
- Contas/provisionamento AWS; S3, SQS, papéis/roles, observabilidade.
- Times consumidores para validar contratos e metas (latência/volume).

## Riscos e Mitigações
- Lacuna na fonte de falsos positivos: definir fonte/sistema e processo de captura.
- Acesso a históricos: plano alternativo de amostragem/parcerias internas.
- Privacidade e viés: revisão de atributos sensíveis e auditoria contínua.
- Custos de inferência: metas de custo/1k transações e testes de otimização.

## Itens a Confirmar
- North Star e 2–3 KPIs de suporte, metas e janelas.
- Throughput alvo (tx/s), SLOs de latência e SLAs de uptime.
- Estrutura de TE40 no resultset e dicionário 3DS↔TE40.
- Estratégia final de correlação (`NRID`) e idempotência (SQS).
- Regras de mascaramento/PII com compliance e owners de dados.

## Referências consultadas
- `documentos recebidos/online-purchase.yaml`
- `reunioes/2025-10-03/pauta_reuniao_dados.md`
- `reunioes/2025-10-03/debriefing_reuniao_dados.md`
- `reunioes/2025-09-30/email_pos_reuniao.md`
- `arquitetura/docs/arquitetura_ml_sagemaker.drawio`

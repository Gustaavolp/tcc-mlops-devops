# Contexto do Projeto de TCC: Integração de MLOps em pipelines DevOps

**Tema Definitivo:** Integração de MLOps em pipelines DevOps: desafios e boas práticas para entrega contínua de modelos de machine learning em produção.

## 1. Visão Geral do Repositório e Arquitetura

Este documento fornece o contexto completo de um repositório real de nível de produção (production-grade) que servirá como estudo de caso para o TCC. O repositório implementa uma arquitetura fim a fim de MLOps integrada com práticas avançadas de DevOps na AWS.

O sistema não foca no desenvolvimento do algoritmo de Machine Learning em si (embora existam scripts de treinamento), mas sim na **engenharia da plataforma** que suporta o ciclo de vida do modelo: desde o provisionamento da infraestrutura via código, passando pelo treinamento automatizado, até o deploy e escalonamento da inferência em Kubernetes.

**Caso de Uso de Negócio Inferido:** O repositório contém documentações (ex: um PPT em `docs/`) que sugerem o uso da plataforma para "Detecção de Fraude / Repasse" ou análise de anomalias estatísticas.

---

## 2. Tecnologias Principais Identificadas no Repositório

O projeto utiliza uma stack tecnológica robusta e Cloud-Native, ideal para demonstrar o "estado da arte" no tema do TCC:

*   **Cloud Provider:** AWS (Amazon Web Services).
*   **Infraestrutura como Código (IaC):** Terraform (`infra/`). Utilizado de forma modular para provisionar redes (VPC), Kubernetes (EKS), filas (SQS), MLflow, API Gateway, etc.
*   **Orquestração de Contêineres:** Kubernetes / Amazon EKS (`k8s/`).
*   **Automação de CI/CD:** AWS CodeBuild (`buildspecs/`). Pipelines YAML definem a construção de imagens Docker, validação de infraestrutura e deploy no K8s.
*   **Plataforma de MLOps (Rastreamento e Model Registry):** MLflow (`infra/modules/mlflow/`). Usado para versionar modelos e registrar métricas de experimentos.
*   **Treinamento de Modelos:** AWS SageMaker e AWS Glue. Scripts Python gerenciam jobs de treinamento.
*   **Automação e Integração (Serverless):** AWS Lambda (`lambdas/`). Destaca-se a lambda `register-best-model`, que implementa a lógica de negócio MLOps para avaliar e promover o melhor modelo treinado com base em métricas.
*   **Escalabilidade Orientada a Eventos:** KEDA (Kubernetes Event-driven Autoscaling) integrado com Amazon SQS (`k8s/dev/keda/`). Permite que os pods de inferência escalem horizontalmente com base no tamanho da fila de requisições.
*   **Desenvolvimento de APIs/Serviços:** Python (provavelmente FastAPI ou Flask) conteinerizado via Docker (`services/inference/` e `services/process/`).
*   **IA Generativa / Análises Avançadas:** Integração com Amazon Bedrock (`agent_bedrock/`) para geração de insights ou relatórios sobre promoções e estatísticas baseados em dados do Athena/S3.

---

## 3. Estrutura de Diretórios e Seu Papel no TCC

A estrutura do repositório reflete a separação de responsabilidades (DevOps vs MLOps) que o TCC busca integrar:

### 3.1. `infra/` (O pilar DevOps/IaC)
Contém todo o código Terraform. A subpasta `modules/` isola a criação de componentes (EKS, VPC, SQS, S3, MLflow, SageMaker). A subpasta `environments/` (dev/staging) mostra como o Terraform é usado para manter paridade entre ambientes.
*   *Relevância para o TCC:* Demonstra a prática de "Infraestrutura Imutável" e como tratar recursos de ML da mesma forma que recursos de software tradicional.

### 3.2. `buildspecs/` (O pilar CI/CD)
Contém as definições de pipeline (AWS CodeBuild). Separados por ambiente (`dev/`, `staging/`) e tipo de tarefa (`docker/`, `infra/`). Exemplo: `buildspecs/dev/docker/inference.yaml` constrói a imagem Docker da API de inferência e faz o push para o ECR.
*   *Relevância para o TCC:* Demonstra a "Entrega Contínua" (Continuous Delivery) automatizando a passagem do código para o artefato pronto para produção.

### 3.3. `k8s/` e `services/` (O pilar de Serving e Escalabilidade)
*   `services/`: Contém o código-fonte (Python) das aplicações que rodam no cluster: `inference/` (carrega o modelo do MLflow e faz predições) e `process/` (possivelmente processa dados brutos antes da inferência). Cada um tem seu `Dockerfile`.
*   `k8s/`: Contém os manifestos Kubernetes para deploy desses serviços. Inclui configurações do **KEDA**, fundamental para mostrar como a inferência escala baseada em eventos (mensagens no SQS).
*   *Relevância para o TCC:* Aborda os "desafios de produção", mostrando como servir o modelo de forma resiliente e escalável.

### 3.4. `lambdas/` (O pilar de Automação MLOps)
Destaca-se a pasta `lambdas/register-best-model/`. O arquivo `best_model_register.py` contém lógica Python que, provavelmente após um job de treinamento, avalia as métricas do MLflow e "promove" o modelo se ele for melhor que o atual.
*   *Relevância para o TCC:* Ilustra perfeitamente a "governança de modelos" e o desafio de criar um loop de feedback automatizado (Continuous Training/Deployment).

### 3.5. `model/` e `glue/` (O pilar de Treinamento/Dados)
Contém scripts (ex: `glue/job_training_test_1.py` e `model/mix_models/script_launch_job_sagemaker.py`) responsáveis por treinar os algoritmos e registrar os resultados (artefatos e métricas) no servidor MLflow provisionado pela infraestrutura.

### 3.6. `agent_bedrock/` (Inovação Adicional)
Contém lambdas que integram dados do AWS Athena com modelos de fundação do AWS Bedrock para gerar relatórios (`promotion/`, `statistics/`). Embora possa ser um escopo secundário para o tema principal, demonstra uma arquitetura avançada de dados.

---

## 4. Como este contexto se alinha aos objetivos do TCC

1.  **Diferenciar ciclos de vida:** O repositório mostra claramente o código da aplicação (`services/`) versionado no Git (DevOps), enquanto os binários/pesos dos modelos e métricas de experimentação vivem no MLflow (MLOps).
2.  **Provisionamento Automatizado:** A vasta pasta `infra/` prova que tudo é provisionado via código, sem cliques no console da nuvem.
3.  **CI/CD para ML:** A combinação de `buildspecs/` (empacotamento Docker) com a lambda `register-best-model` forma um pipeline completo: código altera -> imagem buildada -> modelo treinado -> modelo avaliado -> modelo promovido.
4.  **Escalabilidade em Produção:** O uso do EKS acoplado ao KEDA e SQS responde diretamente ao problema de como manter um sistema preditivo online sob variações extremas de carga, uma das maiores dores da implantação de ML.
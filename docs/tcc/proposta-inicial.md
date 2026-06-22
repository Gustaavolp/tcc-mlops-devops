# Documento de Definição de Projeto de TCC

## 1. Tema Definitivo
Integração de MLOps em pipelines DevOps: desafios e boas práticas para entrega contínua de modelos de machine learning em produção.

## 2. Problema de Pesquisa
Embora a adoção de práticas de DevOps já esteja consolidada para o desenvolvimento de software tradicional, a implantação e a manutenção de modelos de *Machine Learning* (ML) em produção apresentam complexidades singulares. Sistemas de ML dependem não apenas de código, mas da evolução contínua dos dados e das métricas de performance do próprio modelo, o que gera desafios de versionamento, reprodutibilidade e degradação (*model drift*). Grande parte dos projetos de ciência de dados não atinge o ambiente de produção devido à falta de uma ponte estruturada entre os ambientes de experimentação (como *Jupyter Notebooks*) e as operações de TI. Diante desse cenário, a presente pesquisa busca responder: **Como integrar de forma eficiente, escalável e automatizada o ciclo de vida de modelos de Machine Learning (MLOps) em pipelines tradicionais de DevOps, garantindo a entrega contínua e a governança operacional em ambientes de produção complexos?**

## 3. Objetivos

### 3.1. Objetivo Geral
Analisar e demonstrar, por meio de um estudo de caso prático embasado em infraestrutura em nuvem, a implementação de uma arquitetura de MLOps integrada a pipelines de DevOps, identificando os principais desafios técnicos e estabelecendo boas práticas para a entrega e operação contínua de modelos de *Machine Learning*.

### 3.2. Objetivos Específicos
1. **Diferenciar ciclos de vida:** Mapear as diferenças arquiteturais e operacionais entre o ciclo de vida de software tradicional (DevOps) e o ciclo de vida de modelos de aprendizado de máquina (MLOps).
2. **Provisionamento Automatizado (IaC):** Demonstrar a estruturação de infraestrutura como código (utilizando Terraform) para suportar ecossistemas de ML na nuvem, garantindo a paridade entre ambientes de desenvolvimento e produção.
3. **Automação de CI/CD para ML:** Estruturar pipelines de integração e entrega contínuas para o treinamento, empacotamento (containerização) e implantação de serviços preditivos.
4. **Governança e Rastreamento:** Implementar e avaliar práticas de versionamento unificado de código, dados e modelos, utilizando ferramentas de registro e rastreamento de experimentos (como MLflow).
5. **Escalabilidade e Serventia (*Serving*):** Avaliar a implementação de mecanismos de inferência escaláveis e baseados em eventos no Kubernetes, utilizando métricas de filas para autoescalonamento dinâmico.

## 4. Justificativa
### 4.1. Justificativa Técnica, Prática e Acadêmica
O desenvolvimento de sistemas baseados em Inteligência Artificial tem crescido exponencialmente. Contudo, a literatura técnica aponta que desenvolver um modelo preditivo com alta acurácia é apenas uma pequena fração do esforço necessário para construir um sistema de ML em produção (SCULLEY *et al.*, 2015). A desconexão entre os times de ciência de dados e engenharia de software cria o que a indústria chama de "dívida técnica oculta", resultando em processos manuais, lentos e suscetíveis a falhas na hora do *deploy*.

Do ponto de vista **prático e técnico**, este projeto justifica-se pela urgência do mercado em adotar o MLOps não como uma ferramenta isolada, mas como uma extensão natural do DevOps. A utilização de uma pilha tecnológica moderna e orientada a nuvem (*Cloud-Native*) — englobando Kubernetes, Terraform, Docker e serviços gerenciados da AWS — reflete o "estado da arte" das arquiteturas corporativas atuais. Demonstrar a integração dessas tecnologias provê um roteiro técnico valioso para resolver gargalos de escalabilidade (ex: autoescalonamento de inferência baseado em eventos) e de governança (ex: promoção automatizada de modelos baseada em métricas de performance).

Sob a ótica **acadêmica**, o trabalho contribui para o corpo de conhecimento da Engenharia de Software ao transpor conceitos teóricos de integração contínua (CI) e entrega contínua (CD) para a esfera dos dados e modelos (CT - *Continuous Training*). O estudo de caso fornece evidências empíricas sobre os desafios arquiteturais, oferecendo documentação técnica estruturada que pode servir de base para pesquisas futuras sobre resiliência e automação em sistemas de IA.

## 5. Referências Iniciais
1. **SCULLEY, D. et al.** *Hidden Technical Debt in Machine Learning Systems*. Advances in Neural Information Processing Systems (NeurIPS), v. 28, 2015. *(Referência clássica sobre a complexidade de sistemas de ML).*
2. **TREVEIL, M. et al.** *Introducing MLOps: How to Scale Machine Learning in the Enterprise*. 1ª ed. O'Reilly Media, 2020. *(Livro base para conceitos operacionais de MLOps).*
3. **KREUZBERGER, D.; KÜHL, N.; HIRSCHL, S.** *Machine Learning Operations (MLOps): Overview, Definition, and Architecture*. IEEE Access, v. 11, p. 31866-31879, 2023. *(Artigo científico recente que define a arquitetura padrão).*
4. **AMAZON WEB SERVICES (AWS).** *Machine Learning Lens - AWS Well-Architected Framework*. Disponível em: AWS Whitepapers. Acesso em: março de 2026. *(Base de boas práticas corporativas para infraestrutura).*
5. **FOWLER, M.** *Continuous Integration*. MartinFowler.com, 2006. *(Referência fundamental para os conceitos de CI/CD originários da Engenharia de Software).*

## 6. Descrição da Aplicação e Processo
### 6.1. Descrição Preliminar
O projeto prático consiste na engenharia e automação de uma plataforma de *Machine Learning* fim a fim na nuvem. A aplicação não focará no desenvolvimento do algoritmo matemático em si, mas sim na engenharia da plataforma que o suporta. O processo abrangerá desde a automação da infraestrutura subjacente até a disponibilização do modelo preditivo através de uma API escalável e tolerante a falhas, simulando um ambiente real de processamento de dados (como um sistema de detecção de anomalias ou fraudes).

A arquitetura adota um padrão de microsserviços orientados a eventos. O fluxo automatizado garante que novos modelos treinados sejam avaliados e, se apresentarem melhoria nas métricas, sejam automaticamente registrados e preparados para *deploy*. O ambiente de inferência consumirá requisições de forma assíncrona, garantindo alto desempenho mesmo em picos de demanda.

### 6.2. Tecnologias Envolvidas
*   **Infraestrutura e Provisionamento (IaC):** Terraform para criação automatizada e versionada de recursos em múltiplos ambientes (Dev, Staging).
*   **Contêineres e Orquestração:** Docker para empacotamento das aplicações (treinamento e inferência) e Kubernetes (Amazon EKS) para orquestração de contêineres.
*   **Pipelines de CI/CD:** Arquivos de configuração declarativos (Buildspecs) gerenciando construção de imagens, testes e atualização de recursos no Kubernetes.
*   **Rastreamento e Governança de ML (MLOps):** MLflow para registro de parâmetros de treinamento e *Model Registry*. AWS SageMaker e AWS Glue para execução de rotinas de treinamento de dados.
*   **Escalabilidade e Mensageria:** Amazon SQS para enfileiramento de requisições e KEDA (*Kubernetes Event-driven Autoscaling*) para escalonamento horizontal automático dos *pods* de inferência baseado no volume da fila.
*   **Automação *Serverless*:** Funções AWS Lambda para realizar a governança condicional (ex: promoção de modelos baseada em regras de negócio).
*   **Linguagens:** Python (FastAPI/Scripts de automação) e HCL (Terraform).

### 6.3. Delimitação de Escopo Funcional Inicial
O escopo do desenvolvimento e da análise cobrirá as seguintes entregas funcionais:
1.  **Módulo de Infraestrutura:** Criação dos módulos Terraform contemplando a rede (VPC), o cluster Kubernetes (EKS), armazenamento (S3), filas (SQS) e servidores do MLflow.
2.  **Módulo de Integração Contínua:** Implementação de pipelines automatizados que, a cada atualização de código, realizam a construção das imagens Docker dos microsserviços de inferência e as publicam em um repositório seguro (ECR).
3.  **Módulo de Entrega e Treinamento Contínuo:** Automação do ciclo do modelo, onde rotinas de treinamento registram suas métricas no MLflow, seguidas por uma avaliação automatizada (via Lambda) que marca o melhor modelo para produção.
4.  **Módulo de Inferência Escalável:** Implantação de um microsserviço no Kubernetes que escuta as filas de eventos, carrega dinamicamente o modelo aprovado pelo fluxo anterior e escala a capacidade de processamento (via KEDA) conforme o número de mensagens pendentes, demonstrando a robustez do sistema em produção.
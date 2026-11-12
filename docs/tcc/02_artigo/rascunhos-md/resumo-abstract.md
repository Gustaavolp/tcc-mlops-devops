# Resumo e Abstract — TCC MLOps

Textos prontos para inserir no Word.  
Posicionamento no documento: imediatamente após a folha de rosto, antes do Sumário, cada um em página própria.  
Gerado em: 2026-06-22

---

## Formatação no Word (ABNT)

- Título "RESUMO" / "ABSTRACT": centralizado, maiúsculas, negrito, sem numeração de seção
- Corpo: parágrafo único, texto justificado, espaçamento 1,5
- "Palavras-chave:" / "Keywords:": negrito, seguido dos termos separados por ponto e espaço
- Cada um em página separada (quebra de página entre Resumo e Abstract)

---

## RESUMO

Este trabalho apresenta o projeto e a implementação de uma plataforma de MLOps integrada a pipelines de DevOps, desenvolvida e implantada em ambiente de produção real de uma empresa de grande porte do setor de pagamentos eletrônicos, com infraestrutura em nuvem AWS. O objetivo geral consiste em demonstrar como automatizar o ciclo de vida completo de modelos de *Machine Learning* em produção, desde o provisionamento da infraestrutura até o escalonamento dinâmico da inferência. A metodologia adota uma abordagem de pesquisa aplicada com caráter experimental, estruturada em quatro fases: levantamento bibliográfico, desenvolvimento de infraestrutura como código (IaC) com Terraform, implementação de pipelines de integração e entrega contínuas (CI/CD) e treinamento contínuo (CT), e validação experimental por meio de testes de carga. A infraestrutura foi codificada em 15 módulos Terraform organizados em cinco *stacks* independentes. Os pipelines de CI/CD utilizam AWS CodeBuild para construção e publicação de imagens Docker, enquanto o ciclo de vida do modelo é gerenciado por funções AWS Lambda que disparam *jobs* de treinamento no Amazon SageMaker e promovem automaticamente o melhor modelo no MLflow Registry com base em métricas de desempenho. O serviço de inferência, implementado com FastAPI no Amazon EKS, escala horizontalmente por meio do KEDA (*Kubernetes Event-driven Autoscaling*) utilizando a profundidade da fila Amazon SQS como métrica de escalonamento. Os testes de carga evidenciaram que a ausência de *HTTP keepalive* nas conexões entre componentes de rede gerava picos de latência de até 5.217 ms; após a correção, o percentil P95 reduziu-se em 70%, de 1.100 ms para 330 ms, com zero falhas em mais de 6.000 requisições. Conclui-se que a separação arquitetural explícita entre CI/CD e Treinamento Contínuo, aliada à automação *serverless* e ao escalonamento orientado a eventos, constitui uma abordagem eficaz e reproduzível para a entrega contínua de modelos de *Machine Learning* em produção.

**Palavras-chave:** MLOps. DevOps. Kubernetes. Infraestrutura como Código. Entrega Contínua de Modelos. Aprendizado de Máquina.

---

## ABSTRACT

This work presents the design and implementation of an MLOps platform integrated into DevOps pipelines, developed and deployed in a real production environment of a large-scale electronic payments company on AWS cloud infrastructure. The general objective is to demonstrate how to automate the complete lifecycle of Machine Learning models in production, from infrastructure provisioning to dynamic inference scaling. The methodology follows an applied research approach with an experimental design, structured in four phases: literature review, infrastructure-as-code (IaC) development with Terraform, implementation of continuous integration and delivery (CI/CD) and continuous training (CT) pipelines, and experimental validation through load testing. The infrastructure was codified in 15 Terraform modules organized across five independent stacks. CI/CD pipelines use AWS CodeBuild to build and publish Docker images, while the model lifecycle is managed by AWS Lambda functions that trigger Amazon SageMaker training jobs and automatically promote the best-performing model in the MLflow Registry based on performance metrics. The inference service, implemented with FastAPI on Amazon EKS, scales horizontally through KEDA (Kubernetes Event-driven Autoscaling) using Amazon SQS queue depth as the scaling metric. Load tests revealed that the absence of HTTP keepalive in inter-component network connections caused latency spikes of up to 5,217 ms; after the fix, the P95 latency percentile decreased by 70%, from 1,100 ms to 330 ms, with zero failures across more than 6,000 requests. The study concludes that the explicit architectural separation between CI/CD and Continuous Training, combined with serverless automation and event-driven autoscaling, constitutes an effective and reproducible approach for continuous delivery of Machine Learning models in production environments.

**Keywords:** MLOps. DevOps. Kubernetes. Infrastructure as Code. Continuous Model Delivery. Machine Learning.

---

## Notas para a defesa

- O Resumo tem **~250 palavras** — dentro do intervalo típico para TCC (150–500 palavras conforme ABNT NBR 6028).
- Os dois textos são rigorosamente equivalentes: mesmo número de ideias, mesma ordem, sem acréscimos ou omissões entre as versões.
- O resultado do keepalive (−70% no P95) é o dado mais forte para citar na apresentação oral — é concreto, quantificado e inesperado.
- Nenhuma citação bibliográfica aparece no Resumo/Abstract (correto per ABNT).
- As palavras-chave foram escolhidas para cobrir os temas de busca mais prováveis de quem pesquisar o tema: MLOps, DevOps, Kubernetes, IaC, Entrega Contínua e ML.

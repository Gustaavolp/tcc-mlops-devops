# Seção 8 — Conclusão e Trabalhos Futuros

Texto pronto para inserir no Word após a Seção 7 (Resultados e Discussão).  
A Seção de Referências passa a ser Seção 9.  
Gerado em: 2026-06-22

---

## 8 CONCLUSÃO E TRABALHOS FUTUROS

### 8.1 Conclusão

Este trabalho investigou como integrar de forma eficiente e automatizada o ciclo de vida de modelos de *Machine Learning* (MLOps) em pipelines tradicionais de DevOps, garantindo a entrega contínua e a governança operacional em ambientes de produção complexos. A plataforma foi desenvolvida e implantada em ambiente de produção real de uma empresa de grande porte do setor de pagamentos eletrônicos, com infraestrutura em nuvem AWS, Kubernetes (EKS) e serviços gerenciados. Os cinco objetivos específicos definidos na Seção 2.2 foram abordados da seguinte forma:

**(i) Projetar as camadas de integração DevOps/MLOps.** A arquitetura resultante demonstra que DevOps e MLOps operam em camadas com responsabilidades distintas e ferramentas próprias. A camada DevOps, implementada com AWS CodeBuild e *buildspecs* declarativos versionados no repositório, gerencia a construção e publicação das imagens Docker dos serviços de inferência. A camada MLOps, implementada com funções AWS Lambda (*training-launcher* e *register-best-model*), gerencia o ciclo de vida do modelo: disparo de *jobs* de treinamento no SageMaker, rastreamento de experimentos no MLflow e promoção condicional do melhor modelo ao estado de produção. Essa separação arquitetural evita o acoplamento entre a entrega de código e a entrega de modelos — um desafio recorrente identificado pela literatura (SCULLEY et al., 2015; KREUZBERGER et al., 2023) e frequentemente subestimado em implementações reais.

**(ii) Implementar infraestrutura como código (IaC) via Terraform.** A infraestrutura completa foi codificada em Terraform 1.11, organizada em 15 módulos distribuídos em 5 *stacks* independentes: *foundation* (VPC, subnets, IAM), *mlops* (SageMaker MLflow, S3 para artefatos), *platform* (EKS, ECR, SQS, DynamoDB, Kinesis), *platform-k8s* (deployments Kubernetes, KEDA, Ingress) e *platform-lambdas* (funções de automação MLOps). Essa modularização permitiu a criação e destruição independente de cada camada, eliminando dependências circulares e garantindo paridade entre os ambientes DEV e *Staging* (BRIKMAN, 2019; KARIMIBIUKI et al., 2022).

**(iii) Desenvolver pipelines de CI/CD/CT.** Três trilhas de automação foram implementadas: (a) CI/CD — AWS CodeBuild constrói a imagem Docker do serviço de inferência e publica no ECR a cada *commit*; (b) CT (*Continuous Training*) — a Lambda *training-launcher* despacha *jobs* de treinamento XGBoost no SageMaker com dados Parquet do S3, registrando parâmetros e métricas no MLflow; (c) promoção condicional — a Lambda *register-best-model* compara o F1-score do modelo candidato com o modelo em produção e, havendo melhoria, promove automaticamente a nova versão no *MLflow Registry*. O serviço de inferência carrega o modelo diretamente via MLflow, eliminando a necessidade de *endpoints* SageMaker dedicados.

**(iv) Implementar governança via MLflow.** O MLflow foi provisionado como *SageMaker Managed Tracking Server*, solução gerenciada pela AWS que elimina o esforço operacional de manutenção de servidor, mantendo compatibilidade total com a API do MLflow (ZAHARIA et al., 2018). Todos os experimentos de treinamento têm parâmetros, métricas e artefatos registrados automaticamente. O *MLflow Registry* serve como fonte de verdade para a versão do modelo em produção, com *tags* de estado (*stage: production*) gerenciadas pelas funções Lambda de automação. Essa abordagem provê rastreabilidade completa: dado qualquer *deploy*, é possível identificar o experimento de origem, o *dataset* utilizado, as métricas de validação e o código que o gerou.

**(v) Validar o escalonamento via KEDA.** O KEDA (*Kubernetes Event-driven Autoscaling*) foi configurado para escalar os *pods* de inferência com base na profundidade da fila SQS FIFO, substituindo o escalonamento baseado em CPU — inadequado para cargas de inferência ML, que são bursty e têm perfil de consumo diferente de cargas CPU-intensivas tradicionais. Os testes de carga com Locust demonstraram que, após a otimização de *HTTP keepalive*, o serviço atingiu **P95 de 330 ms** no ambiente DEV e **P95 de 124 ms** no ambiente *Staging*, ambos abaixo da meta de 500 ms, com **zero falhas** em mais de 11.000 requisições testadas entre os dois ambientes.

**Achado não antecipado: impacto crítico do *HTTP keepalive*.** O resultado de maior relevância prática emergiu da investigação de anomalias de latência: a ausência de *HTTP keepalive* nas conexões entre componentes da cadeia de rede (API Gateway → NLB → ALB → pod EKS) gerava picos de até **5.217 ms** em 3% das requisições. A habilitação do *keepalive* reduziu o P95 de **1.100 ms para 330 ms** — melhoria de 70% — sem qualquer alteração em infraestrutura, modelo ou algoritmo. Esse achado evidencia que, em arquiteturas ML com múltiplas camadas de rede, problemas de latência podem ser causados por fatores de rede completamente alheios ao modelo, e que testes de carga com carga concorrente são essenciais para revelar comportamentos invisíveis em testes unitários ou sequenciais.

Em resposta à pergunta de pesquisa, conclui-se que a integração eficiente de MLOps em pipelines DevOps requer: (a) separação arquitetural explícita entre CI/CD e CT; (b) automação *serverless* para os eventos de ciclo de vida do modelo; (c) IaC modularizado por domínio funcional; (d) governança centralizada via *Model Registry*; e (e) testes de carga com carga concorrente e *payloads* reais como parte do processo de validação — não como etapa opcional.

---

### 8.2 Contribuições

Este trabalho oferece as seguintes contribuições ao corpo de conhecimento da Engenharia de Software e MLOps:

1. **Evidência empírica sobre *HTTP keepalive* em sistemas de inferência ML:** demonstração quantitativa de que a ausência de *keepalive* em arquiteturas com múltiplos intermediários de rede causa degradação severa e intermitente de latência, com impacto desproporcional nos percentis superiores (P95, P99).

2. **Padrão arquitetural CI/CD + CT desacoplados:** documentação de uma arquitetura prática na qual o pipeline de CI/CD (CodeBuild) e o ciclo de vida do modelo (Lambda + SageMaker) são mecanismos independentes com fronteiras claras — contrariando abordagens que tentam unificar ambos em um único pipeline.

3. **Referência de implementação MLOps *cloud-native* completa:** repositório público com código real de um sistema de detecção de fraude em escala corporativa, cobrindo todas as camadas do stack MLOps (IaC, CI/CD, CT, *serving*, autoscaling, governança e observabilidade com IA generativa).

4. **Validação de escalonamento orientado a eventos (KEDA+SQS) para inferência ML:** evidência prática de que a profundidade de fila é uma métrica de escalonamento mais adequada que CPU para cargas de inferência com demanda variável.

---

### 8.3 Limitações

**Throughput de 100 RPS não validado experimentalmente.** Os testes Locust disponíveis foram executados com 50 usuários virtuais, atingindo ~47 RPS. O teste com 100 usuários (que projetaria 100 RPS conforme a configuração de *constant_throughput*) não foi executado dentro do escopo documentado deste trabalho.

**Comportamento do KEDA sob carga de *spike* não capturado.** Os testes foram realizados com carga estável, sem variação abrupta de throughput. O tempo de reação do KEDA para escalar réplicas em resposta a picos súbitos de fila não foi medido diretamente.

**Treinamento contínuo (CT) sem gatilho automático por degradação de métricas.** O ciclo de CT, na implementação atual, requer a invocação manual da Lambda *training-launcher*. A detecção automática de *model drift* como gatilho de retreinamento não foi implementada no escopo deste trabalho.

**Ambiente de validação único (AWS).** A arquitetura foi projetada e validada exclusivamente na AWS. A portabilidade dos padrões para outros provedores de nuvem (GCP, Azure) ou ambientes *on-premise* não foi avaliada.

---

### 8.4 Trabalhos Futuros

Com base nas limitações identificadas e nas oportunidades observadas durante a implementação, propõem-se as seguintes extensões:

**1. Validação de throughput de 100 RPS e comportamento do KEDA sob carga de *spike*.** Executar os cenários *target* (100 usuários) e *spike* (200 usuários, 1 minuto) previstos no *locustfile.py*, monitorando simultaneamente o número de réplicas escaladas pelo KEDA, a latência por percentil e o tempo de reação ao pico.

**2. Implementação de detecção automática de *concept drift*.** Integrar um mecanismo de monitoramento de distribuição de *scores* — comparando a distribuição atual do modelo com a distribuição de referência do treino — que acione automaticamente a Lambda *training-launcher* quando o desvio ultrapassar um limiar configurável (GAMA et al., 2014). O componente *Statistics Reporter* já coleta os dados necessários para essa análise.

**3. Implantação com *Canary Release* para modelos.** Substituir a promoção imediata (*blue/green*) por uma estratégia de *canary*, na qual a nova versão do modelo recebe uma fração do tráfego (ex: 10%) antes da promoção total. Isso permitiria detectar regressões em produção com impacto controlado.

**4. *Benchmark* KEDA vs. HPA baseado em CPU.** Comparar quantitativamente o comportamento do KEDA (baseado em profundidade de fila SQS) com o HPA (*Horizontal Pod Autoscaler*) baseado em CPU, medindo tempo de reação, número de réplicas provisionadas e custo por requisição em cenários de carga variável.

**5. Extensão do componente Bedrock para *drift* conversacional.** Evoluir o *lambda* de coleta de dados (atualmente projetado como *action group*) para um Bedrock Agent conversacional completo, permitindo que analistas de fraude consultem o status do modelo, métricas de *drift* e histórico de promoções em linguagem natural.

**6. Multi-região e recuperação de desastres.** Projetar a replicação da pilha MLOps para uma segunda região AWS (*sa-east-1* → *us-east-1*), com *failover* automatizado via Route 53 e replicação de artefatos MLflow entre buckets S3, avaliando o impacto no SLA de inferência durante a transição.

---

*Nota de implementação (não vai para o artigo):*  
*Esta seção é a Seção 8 do artigo final. A Seção 6 (Resultados e Discussão — secao-resultados-discussao.md) precisa ser inserida antes desta. As Referências passam a ser Seção 9.*

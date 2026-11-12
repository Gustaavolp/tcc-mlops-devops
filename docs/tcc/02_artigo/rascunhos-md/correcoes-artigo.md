# Correções Pendentes — Artigo TCC MLOps

Documento de referência para aplicar no arquivo Word fonte do artigo.  
Gerado em: 2026-06-22

---

## Correção 1 — Seção 4 (Metodologia), item 3

**Localização:** Seção 4 "METODOLOGIA", terceiro item da lista numerada (página 5 do PDF).

**Texto ATUAL (errado):**
> 3. **Implementação do Pipeline:** Desenvolvimento de fluxos de CI/CD via GitHub Actions e integração com MLflow para governança. O pipeline será responsável pelo treinamento automático, avaliação de métricas e promoção condicional de modelos.

**Texto CORRETO:**
> 3. **Implementação do Pipeline:** Desenvolvimento de fluxos de CI/CD via AWS CodeBuild, com buildspecs declarativos versionados no repositório, e integração com MLflow para governança. O pipeline é responsável pela construção e publicação das imagens Docker dos serviços de inferência, enquanto a promoção condicional de modelos é automatizada via função AWS Lambda (`register-best-model`), que avalia métricas de experimentos e eleva o melhor modelo ao status de produção no MLflow Registry.

**Motivo da correção:**  
GitHub Actions nunca foi utilizado no projeto. A ferramenta de CI/CD efetivamente implementada é o **AWS CodeBuild**, cujo buildspec está em `buildspecs/iam-policy-setup.yaml`. Além disso, o texto original confundia o pipeline de CI/CD (build de imagens) com o ciclo de promoção de modelos (Lambda), que são mecanismos distintos.

---

## Correção 2 — Seção 5.1 (Descrição da Abordagem)

**Localização:** Seção 5.1 "Descrição da Abordagem" (página 6 do PDF).

**Texto ATUAL (impreciso):**
> O fluxo inicia-se com o commit do código. O pipeline realiza o *build*, dispara o treinamento no AWS SageMaker e registra métricas no MLflow. Um módulo de decisão avalia a performance; se aprovado, o modelo é implantado no EKS. O escalonador KEDA monitora o tamanho da fila SQS e ajusta os *pods* conforme a necessidade de processamento.

**Texto CORRETO:**
> O fluxo opera em duas trilhas paralelas e complementares. Na **trilha de serving**, um commit no repositório aciona o AWS CodeBuild, que constrói a imagem Docker do serviço de inferência (FastAPI), publica no Amazon ECR e atualiza o deployment no Amazon EKS via `kubectl`. Na **trilha de MLOps**, a função Lambda `training-launcher` dispara um SageMaker Training Job que treina o modelo XGBoost com dados Parquet do S3, registrando parâmetros e métricas no MLflow. Ao término do treinamento, a função Lambda `register-best-model` compara automaticamente as métricas do experimento com o modelo em produção e, se houver melhoria, promove o novo modelo no MLflow Registry. O serviço de inferência carrega o modelo diretamente via MLflow, sem necessidade de SageMaker Endpoint. O escalonador KEDA monitora a profundidade da fila SQS FIFO e ajusta o número de réplicas dos *pods* de inferência conforme a demanda real.

**Motivo da correção:**  
O texto original omitia a distinção entre os dois pipelines (CodeBuild para serving vs. Lambda para MLOps), sugeria equivocadamente que o mesmo pipeline faz build e dispara treinamento, e não mencionava que o modelo é carregado via MLflow (e não via SageMaker Endpoint, que não é utilizado nesta arquitetura).

---

## Correção 3 — `diagrama-arquitetura.md` (Figura 1), aplicada em 2026-09-11

**Contexto:** o texto do artigo (Seção 3.3/3.4 e Fluxo 1) já estava correto desde a última revisão (2026-07-04), mas o arquivo-fonte do diagrama (`diagrama-arquitetura.md`), usado para gerar a Figura 1, ainda não tinha recebido a mesma correção. Três problemas foram corrigidos:

1. **Versão do Terraform:** o nó `TF` do diagrama dizia "Terraform 1.11"; o código real (`infra/**/backend.tf`) usa `required_version = "~> 1.14.0"`. Corrigido para "Terraform 1.14".
2. **ALB inexistente na cadeia de rede:** o diagrama mostrava `API Gateway → NLB → ALB → EKS`. Não existe Application Load Balancer nessa cadeia — verificado em `infra/modules/nlb/main.tf` (único load balancer do projeto, `load_balancer_type = "network"`) e nos `TargetGroupBinding` em `k8s/*/inference/target-group-binding.yaml`, que apontam direto para os pods via NLB (`targetType: ip`). Corrigido para `API Gateway → VPC Link → NLB → EKS`, sem ALB.
3. **HPA da Inferência ausente:** o diagrama só representava o KEDA (que escala o Process via profundidade de fila SQS), dando a entender que o Inference Service também escalaria por KEDA. Na realidade o Inference Service usa um **HPA tradicional baseado em CPU** (`k8s/*/inference/hpa.yaml`: min 8 / max 10 réplicas, threshold 50%). Adicionado o nó HPA escalando o Inference Service, mantendo o KEDA associado apenas ao Process.

**Motivo:** garantir que a Figura 1 e sua legenda representem fielmente a arquitetura real antes da entrega de desenvolvimento de 2026-09-11 ao orientador.

---

## Resumo das mudanças por seção

| Seção | Problema | Mudança |
|-------|----------|---------|
| 4 — Metodologia, item 3 | "GitHub Actions" — ferramenta errada | → "AWS CodeBuild com buildspecs declarativos" |
| 4 — Metodologia, item 3 | Confunde CI/CD com promoção de modelos | → Separar: CodeBuild (build) vs. Lambda (promoção) |
| 5.1 — Descrição da Abordagem | "O pipeline realiza o build e dispara o treinamento" — mesclado em um pipeline só | → Distinguir trilha de serving (CodeBuild) da trilha MLOps (Lambda) |
| 5.1 — Descrição da Abordagem | Não menciona que o modelo é carregado via MLflow | → Explicitar: sem SageMaker Endpoint; carregado diretamente via MLflow |

---

## O que NÃO precisa mudar

- **Seção 2.2 (Objetivos):** A menção a "pipelines de CI/CD/CT" está correta — é terminologia, não ferramenta.
- **Seção 3.3 (IaC):** A descrição do Terraform no corpo do artigo está precisa e completa (Terraform 1.14, backend S3 com lock nativo, sem DynamoDB).
- **Seção 3.4 (KEDA):** A descrição do KEDA com EKS e SQS está correta e alinhada com a implementação real.
- **Figura 1 (Diagrama):** Ver Correção 3 abaixo — o arquivo-fonte `diagrama-arquitetura.md` estava desatualizado em relação ao artigo e foi corrigido em 2026-09-11.
- **Seção 6 (Referências):** As 8 referências estão corretas. Observação: a referência [6] aparece como "KA-RIMIBIUKI" no corpo do texto (seção 3.3) mas como "KARIMIBIUKI" na lista — verificar hifenização na citação.

---

## Expansão do Referencial Teórico — 7 novas referências (Task #17)

O artigo possui **8 referências** e o mínimo exigido é **15**. As 7 referências abaixo completam esse mínimo. Todas são obras reais e verificáveis, selecionadas para cobrir lacunas bibliográficas nos temas já tratados no texto (CI/CD, DevOps, MLflow, *model drift*, produção de ML, Terraform e Kubernetes).

### Referências a adicionar na Seção 6 (em ordem alfabética por sobrenome)

---

**BRIKMAN, Y.** **Terraform: Up & Running: Writing Infrastructure as Code**. 2. ed. Sebastopol: O'Reilly Media, 2019.

> **Onde citar no texto:** Seção 3.3 (Infraestrutura como Código), ao mencionar Terraform. Atualmente a seção só cita KARIMIBIUKI et al. (2022). Brikman é a referência canônica para Terraform em IaC.
>
> **Sugestão de frase:** *"A modularização da infraestrutura em stacks independentes por domínio (foundation, mlops, platform) segue as boas práticas de organização descritas por Brikman (2019), permitindo que cada stack seja aplicada de forma isolada e versionada."*

---

**BRECK, E.; CAIN, S.; NIELSEN, E.; SALIB, M.; SCULLEY, D.** The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction. In: **IEEE INTERNATIONAL CONFERENCE ON BIG DATA (BIG DATA)**, 5., 2017, Boston. *Anais* [...]. Piscataway: IEEE, 2017. p. 1123–1132.

> **Onde citar no texto:** Seção 3.1 (Dívida Técnica em Sistemas de ML), como desdobramento de Sculley et al. (2015). BRECK et al. propõem um *rubric* concreto para avaliar prontidão de modelos para produção.
>
> **Sugestão de frase:** *"Breck et al. (2017) operacionalizam esse conceito por meio do ML Test Score, um conjunto de testes categorizados em dados, modelos, infraestrutura e monitoramento, que serve como critério objetivo de prontidão para produção."*

---

**GAMA, J.; ŽLIOBAITĖ, I.; BIFET, A.; PECHENIZKIY, M.; BOUCHACHIA, A.** A Survey on Concept Drift Adaptation. **ACM Computing Surveys**, v. 46, n. 4, artigo 44, p. 1–37, abr. 2014.

> **Onde citar no texto:** Seção 3.2 (CT — Treinamento Contínuo), ao mencionar degradação de modelos e *model drift*. O artigo cita o problema de *drift* mas não tem nenhuma referência sobre o fenômeno.
>
> **Sugestão de frase:** *"A necessidade de Treinamento Contínuo (CT) surge do fenômeno de* concept drift*, no qual a distribuição estatística dos dados de entrada muda ao longo do tempo, degradando o desempenho do modelo em produção (GAMA et al., 2014)."*

---

**HIGHTOWER, K.; BURNS, B.; BEDA, J.** **Kubernetes: Up and Running: Dive into the Future of Infrastructure**. 3. ed. Sebastopol: O'Reilly Media, 2022.

> **Onde citar no texto:** Seção 3.4 (KEDA e Autoscaling Orientado a Eventos), ao introduzir o Kubernetes como base do autoscaling. O artigo descreve KEDA sobre EKS sem nenhuma referência a Kubernetes.
>
> **Sugestão de frase:** *"O Amazon EKS provê um plano de controle Kubernetes gerenciado, abstraindo a operação do cluster e permitindo que a equipe foque nas cargas de trabalho (HIGHTOWER; BURNS; BEDA, 2022)."*

---

**HUMBLE, J.; FARLEY, D.** **Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation**. Boston: Addison-Wesley Professional, 2010.

> **Onde citar no texto:** Seção 3 (Referencial Teórico — pilar de CI/CD), como obra fundacional que complementa Fowler (2006) e formaliza o conceito de *Continuous Delivery*.
>
> **Sugestão de frase:** *"Humble e Farley (2010) formalizaram o conceito de* Continuous Delivery*, estabelecendo que todo artefato de software deve ser entregável a qualquer momento — premissa que o MLOps estende ao ciclo de vida dos modelos de Machine Learning."*

---

**KIM, G.; HUMBLE, J.; DEBOIS, P.; WILLIS, J.** **The DevOps Handbook: How to Create World-Class Agility, Reliability, and Security in Technology Organizations**. Portland: IT Revolution Press, 2016.

> **Onde citar no texto:** Seção 1 (Introdução) e/ou Seção 2.1 (Problema de Pesquisa), ao contextualizar o movimento DevOps que antecede e motiva o MLOps. O artigo discute integração DevOps/MLOps sem nenhuma referência ao DevOps em si.
>
> **Sugestão de frase:** *"O movimento DevOps consolidou a cultura de colaboração entre desenvolvimento e operações por meio de automação, medição e compartilhamento (KIM et al., 2016), princípios que o MLOps incorpora e estende ao contexto de sistemas de Machine Learning."*

---

**ZAHARIA, M. et al.** Accelerating the Machine Learning Lifecycle with MLflow. **IEEE Data Engineering Bulletin**, v. 41, n. 4, p. 39–45, dez. 2018.

> **Onde citar no texto:** Seção 3.2 (rastreamento de experimentos e registro de modelos) e Seção 5.1 (uso do MLflow na solução). O artigo menciona MLflow em múltiplas seções sem nenhuma referência à publicação original.
>
> **Sugestão de frase:** *"O MLflow, proposto por Zaharia et al. (2018), é uma plataforma open-source que padroniza o rastreamento de experimentos, o empacotamento de modelos e o registro centralizado de versões, sendo utilizado neste trabalho via SageMaker Managed Tracking Server."*

---

### Contagem final de referências

| # | Autores | Ano | Tema coberto |
|---|---------|-----|--------------|
| 1 | SCULLEY et al. | 2015 | Dívida técnica em ML |
| 2 | TREVEIL et al. | 2020 | Introdução ao MLOps |
| 3 | KREUZBERGER et al. | 2023 | Arquitetura MLOps |
| 4 | AWS | 2026 | AWS Well-Architected ML |
| 5 | FOWLER | 2006 | Continuous Integration |
| 6 | KARIMIBIUKI et al. | 2022 | IaC para ML |
| 7 | MÄKINEN et al. | 2021 | Adoção de MLOps |
| 8 | GOOGLE CLOUD | 2023 | MLOps pipelines |
| **9** | **BRIKMAN** | **2019** | **Terraform / IaC** |
| **10** | **BRECK et al.** | **2017** | **Prontidão ML para produção** |
| **11** | **GAMA et al.** | **2014** | **Concept drift / model drift** |
| **12** | **HIGHTOWER et al.** | **2022** | **Kubernetes** |
| **13** | **HUMBLE; FARLEY** | **2010** | **Continuous Delivery** |
| **14** | **KIM et al.** | **2016** | **DevOps Handbook** |
| **15** | **ZAHARIA et al.** | **2018** | **MLflow** |

**Total: 15 referências — mínimo atingido.**

---

### Referência adicional (Task #16 — componente Bedrock)

Após definir o escopo do Bedrock, identificou-se a necessidade de uma 16ª referência para embasar o uso de IA generativa como ferramenta de observabilidade:

**AMAZON WEB SERVICES (AWS).** *Amazon Bedrock User Guide*. Disponível em: AWS Documentation. Acesso em: jun. 2026.

> **Onde citar:** Seção 5.1 (ou subseção 5.3 se o orientador aprovar) ao descrever o componente de observabilidade generativa.
>
> **Sugestão de frase:** *"O Amazon Bedrock é um serviço gerenciado da AWS que disponibiliza modelos de linguagem de grande escala (LLMs) de múltiplos provedores via API unificada, eliminando a necessidade de provisionamento de infraestrutura de inferência (AWS, 2026)."*

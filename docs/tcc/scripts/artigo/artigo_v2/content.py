# -*- coding: utf-8 -*-
# Conteúdo do artigo. Marcação inline: {b}..{/b} negrito, {i}..{/i} itálico,
# {ref:ID} referência cruzada automática (campo REF) para tabela/quadro/figura.

TITLE = ("INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS PRÁTICAS PARA "
         "ENTREGA CONTÍNUA DE MODELOS DE MACHINE LEARNING EM PRODUÇÃO")

AUTHORS = [
    ("Gustavo Liebl Pereira",
     "Graduando em Engenharia de Software, Universidade do Contestado (UnC). Mafra. "
     "Santa Catarina. Brasil. E-mail: gustavo.liebl@aluno.unc.br"),
    ("Marcelo Semmer",
     "Professor orientador, Universidade do Contestado (UnC). Mafra. Santa Catarina. "
     "Brasil. E-mail: marcelo.semmer@professor.unc.br"),
]

RESUMO = (
    "A transição de modelos de {i}Machine Learning{/i} (ML) da experimentação para a operação "
    "contínua exige práticas que o DevOps tradicional não cobre, como versionamento de modelos, "
    "retreinamento e governança. Apresenta-se o projeto e a implementação de uma "
    "plataforma de MLOps integrada a {i}pipelines{/i} DevOps, desenvolvida para a detecção de fraude "
    "em compras online de uma empresa do setor de pagamentos eletrônicos, em nuvem AWS. O objetivo é "
    "automatizar o ciclo de vida do modelo, da infraestrutura à inferência. Trata-se de pesquisa aplicada, de caráter experimental e construtivo: a infraestrutura "
    "foi codificada em 15 módulos Terraform organizados em cinco {i}stacks{/i}; {i}pipelines{/i} de "
    "CI/CD constroem, testam e implantam os serviços; uma cadeia orientada a eventos retreina o modelo "
    "XGBoost e promove no MLflow apenas versões com F1-score superior; e a inferência, em FastAPI no "
    "Amazon EKS, escala por CPU, enquanto o processamento assíncrono escala pela profundidade de fila "
    "via KEDA. A validação, restrita aos ambientes de desenvolvimento e homologação, compreendeu duas "
    "sessões de carga com 50 usuários virtuais e testes sequenciais com {i}payloads{/i} reais: não houve "
    "falhas em 12.110 requisições, e a segunda sessão atingiu P95 de 330 ms, abaixo da meta de 500 ms, "
    "enquanto a primeira, em fase de aquecimento, não a atingiu. A vazão de 100 requisições por segundo "
    "e o comportamento do escalonamento sob picos não foram validados. Conclui-se que a separação entre "
    "CI/CD e treinamento contínuo é viável e preserva a governança do modelo, mas sua eficácia em "
    "produção requer avaliação adicional."
)
PALAVRAS = "MLOps; DevOps; Infraestrutura como Código; Kubernetes; Entrega Contínua; Aprendizado de Máquina."

ABSTRACT = (
    "Moving Machine Learning (ML) models from experimentation to continuous operation requires "
    "practices that traditional DevOps does not cover, such as model versioning, retraining and "
    "governance. This work presents the design and implementation of an MLOps platform integrated into "
    "DevOps pipelines, developed for online purchase fraud detection at an electronic payments company, "
    "on the AWS cloud. The goal is to automate the model lifecycle, from infrastructure to inference. This is applied research with an experimental and constructive design: the "
    "infrastructure was codified in 15 Terraform modules organized into five stacks; CI/CD pipelines "
    "build, test and deploy the services; an event-driven chain retrains the XGBoost model and promotes "
    "in MLflow only versions with a higher F1-score; and the inference service, built with FastAPI on "
    "Amazon EKS, scales on CPU, while asynchronous processing scales on queue depth through KEDA. "
    "Validation, restricted to the development and staging environments, comprised two load sessions "
    "with 50 virtual users and sequential tests with real payloads: there were no failures in 12,110 "
    "requests, and the second session reached a P95 of 330 ms, below the 500 ms target, while the first, "
    "still warming up, did not. Throughput of 100 requests per second and autoscaling behavior under "
    "spikes were not validated. The study concludes that separating CI/CD from continuous training is "
    "feasible and preserves model governance, but its effectiveness in production requires further "
    "evaluation."
)
KEYWORDS = "MLOps; DevOps; Infrastructure as Code; Kubernetes; Continuous Delivery; Machine Learning."

# ---------------------------------------------------------------------------
# Corpo
# ---------------------------------------------------------------------------
BODY = [
("h1", "1 INTRODUÇÃO"),
("p", "Uma empresa de grande porte do setor de pagamentos eletrônicos buscava evoluir sua solução de "
      "detecção de fraude em compras online, até então um produto mínimo viável (MVP), para um motor de "
      "inferência operacional, sujeito a requisitos não funcionais de latência, disponibilidade e vazão. "
      "A situação ilustra um gargalo recorrente da Engenharia de Software: a transição de um modelo "
      "experimental para um sistema produtivo resiliente. Diferentemente do {i}software{/i} "
      "convencional, sistemas de {i}Machine Learning{/i} (ML) dependem de dados que mudam ao longo do "
      "tempo e exigem acompanhamento contínuo do desempenho do modelo, e não apenas do código "
      "(Sculley et al., 2015)."),
("p", "Este trabalho documenta a contribuição do autor, responsável pela frente de infraestrutura e "
      "DevOps do projeto, na construção de uma plataforma que integra práticas de MLOps ({i}Machine "
      "Learning Operations{/i}) a {i}pipelines{/i} DevOps. O modelo de classificação foi desenvolvido "
      "pela equipe de ciência de dados e não é objeto de avaliação; o foco recai sobre a automação do "
      "ciclo de vida do modelo, do provisionamento da infraestrutura como código (IaC) ao escalonamento "
      "da inferência em nuvem."),

("h2", "1.1 Problema de pesquisa"),
("p", "Os critérios de aceitação da fase de validação foram definidos pela equipe do projeto a partir "
      "dos requisitos não funcionais do cliente: latência P95 inferior a 500 ms, P99 inferior a 1.000 ms, "
      "taxa de falhas inferior a 1% e vazão de ao menos 100 requisições por segundo (req/s) no ambiente "
      "de testes. Esses critérios avaliam sessões de teste delimitadas e não equivalem à disponibilidade "
      "operacional, cuja aferição exigiria monitoramento longitudinal em produção, nem ao requisito de "
      "vazão de produção do cliente, de ordem de grandeza superior. Somam-se a eles desafios próprios de "
      "ML: a degradação do modelo diante de mudanças na distribuição dos dados, o {i}concept drift{/i} "
      "(Gama et al., 2014), e a dificuldade de levar modelos da experimentação à operação (Kreuzberger; "
      "Kühl; Hirschl, 2023). Diante disso, busca-se responder: como integrar de forma automatizada o "
      "ciclo de vida de modelos de ML a {i}pipelines{/i} DevOps, de modo a atender aos critérios de "
      "aceitação definidos para o serviço de inferência?"),

("h2", "1.2 Objetivos"),
("p", "O objetivo geral é desenvolver e implementar uma arquitetura de MLOps integrada a "
      "{i}pipelines{/i} DevOps, que automatize a entrega e a operação contínua de modelos. Os objetivos "
      "específicos são: (i) projetar as camadas de integração entre DevOps e MLOps; (ii) implementar a "
      "infraestrutura como código com Terraform; (iii) desenvolver {i}pipelines{/i} de integração, "
      "entrega e treinamento contínuos (CI/CD/CT); (iv) implementar a governança de modelos com MLflow; "
      "e (v) configurar o escalonamento da inferência e do processamento assíncrono e avaliar o "
      "desempenho do serviço de inferência sob carga."),

("h2", "1.3 Referencial teórico"),
("p", "{b}Dívida técnica em sistemas de ML.{/b} Segundo Sculley et al. (2015), o código de ML é uma "
      "pequena fração de um sistema produtivo; o esforço maior está em configuração, dados e "
      "monitoramento. Breck et al. (2017) operacionalizam esse cuidado com o {i}ML Test Score{/i}, "
      "conjunto de testes de prontidão para produção."),
("p", "{b}DevOps e entrega contínua.{/b} O DevOps aproxima desenvolvimento e operações por meio de "
      "automação e {i}feedback{/i} contínuo (Kim et al., 2016). A integração contínua (Fowler, 2006) e a "
      "entrega contínua (Humble; Farley, 2010) tornam cada alteração de código potencialmente implantável, "
      "por meio de {i}pipelines{/i} automatizados de construção, teste e implantação."),
("p", "{b}MLOps e treinamento contínuo.{/b} O MLOps estende esses princípios a dados e modelos, "
      "versionando código, modelos e dados (Kreuzberger; Kühl; Hirschl, 2023) e instituindo governança "
      "sobre quais versões chegam à operação (Treveil et al., 2020). Seu diferencial é o treinamento "
      "contínuo ({i}Continuous Training{/i}, CT), que retreina o modelo de forma automatizada; um "
      "{i}pipeline{/i} de CT independente do CI/CD caracteriza os níveis mais maduros de automação "
      "(Google Cloud, 2023). O MLflow (Zaharia et al., 2018) apoia esse ciclo com rastreamento de "
      "experimentos e registro de modelos ({i}Model Registry{/i})."),
("p", "{b}Infraestrutura como código e escalonamento.{/b} A IaC trata a infraestrutura como "
      "{i}software{/i} versionado e reproduzível (Morris, 2020); no Terraform, a modularização em "
      "{i}stacks{/i} por domínio limita o impacto de cada alteração (Brikman, 2019). No Kubernetes, o "
      "{i}Horizontal Pod Autoscaler{/i} (HPA) ajusta o número de réplicas por métricas de recursos, como "
      "CPU (Burns et al., 2022), e o KEDA estende esse mecanismo a métricas de eventos externos, como a "
      "profundidade de filas (KEDA, 2026)."),
("p", "{b}Trabalhos relacionados.{/b} Kreuzberger, Kühl e Hirschl (2023) consolidam, por revisão "
      "sistemática, uma arquitetura de referência para MLOps, sem avaliação empírica de uma "
      "implementação. Mäkinen et al. (2021) identificam, por levantamento com cientistas de dados, as "
      "funcionalidades de MLOps mais demandadas, entre elas o monitoramento de degradação do modelo. Em "
      "relação a ambos, este trabalho oferece o relato de uma implementação concreta, com o padrão de "
      "separação entre CI/CD e CT, e uma avaliação quantitativa de desempenho limitada aos ambientes de "
      "desenvolvimento e homologação; trata-se, portanto, de evidência complementar, e não de uma "
      "avaliação em produção."),

("h1", "2 MATERIAL E MÉTODOS"),
("h2", "2.1 Caracterização da pesquisa"),
("p", "Trata-se de pesquisa aplicada, de caráter experimental e construtivo: o sistema implementado é, "
      "ao mesmo tempo, o artefato produzido e o instrumento de validação. O trabalho foi desenvolvido no "
      "contexto de um projeto profissional, com autorização formal da empresa para uso acadêmico; sua "
      "identificação é omitida por confidencialidade. A pesquisa seguiu quatro etapas: (1) levantamento "
      "bibliográfico nas bases IEEE Xplore, ACM Digital Library e Google Scholar, que apontou como "
      "lacunas o tratamento de CI/CD e CT como um único fluxo e o uso ainda pouco documentado de "
      "escalonamento orientado a eventos; (2) projeto e codificação da infraestrutura; (3) implementação "
      "dos {i}pipelines{/i}; e (4) validação experimental. Os arquivos de IaC, os manifestos Kubernetes, "
      "os scripts e os relatórios brutos de teste estão em repositório privado e versionado do projeto; "
      "por conterem identificadores de contas e credenciais da empresa, não são publicados, mas podem ser "
      "apresentados à banca sem dados sensíveis."),

("h2", "2.2 Infraestrutura como código"),
("p", "A infraestrutura foi codificada em Terraform 1.14, em 15 módulos reutilizáveis (vpc, s3, eks, "
      "ecr, sqs, dynamodb, lambda, mlflow, sagemaker-studio, api-gateway, nlb, firehose, glue, athena e "
      "bedrock-agent), instanciados por cinco {i}stacks{/i} independentes por ambiente, aplicadas na ordem "
      "do {ref:q1}. Cada módulo é utilizado por exatamente uma {i}stack{/i}; a {i}stack{/i} platform-k8s "
      "não usa módulos próprios e instala, via Helm, os complementos do {i}cluster{/i}."),
("quadro", dict(id="q1", title="Stacks Terraform, módulos e responsabilidades",
    widths=[900, 1650, 2850, 3672],
    header=["Ordem", "Stack", "Módulos", "Responsabilidade"],
    rows=[
        ["1", "foundation", "vpc, s3", "VPC com sub-redes públicas e privadas em duas zonas de disponibilidade; 7 buckets S3 por ambiente"],
        ["2", "mlops", "mlflow, sagemaker-studio", "MLflow Tracking Server gerenciado pelo SageMaker; domínio SageMaker Studio"],
        ["3", "platform", "eks, ecr, sqs, dynamodb, firehose, api-gateway, nlb, glue, athena, bedrock-agent", "Cluster EKS 1.32, 6 repositórios ECR, filas SQS FIFO, DynamoDB, Firehose, API Gateway, NLB, Glue, Athena e agente Bedrock"],
        ["4", "platform-k8s", "— (charts Helm)", "metrics-server, Cluster Autoscaler, AWS Load Balancer Controller e KEDA 2.18.3"],
        ["5", "platform-lambdas", "lambda (3 instâncias)", "Funções Lambda conteinerizadas etl-delta-filter, training-launcher e register-best-model e seus gatilhos"],
    ],
    source="Fonte: elaborado pelo autor (2026).")),
("p", "Os sete {i}buckets{/i} S3 por ambiente (data-raw, data-processed, models, logs, resources, "
      "reports-promotion e reports-statistics) isolam responsabilidades no {i}data lake{/i}. O estado de "
      "cada {i}stack{/i} é armazenado em {i}backend{/i} S3 com bloqueio nativo (use_lockfile), e as "
      "{i}stacks{/i} superiores consomem as saídas das inferiores via terraform_remote_state. Os dois "
      "ambientes, desenvolvimento (DEV, us-east-1) e homologação (Staging, sa-east-1), replicam as cinco "
      "{i}stacks{/i} de forma independente. As duas funções Lambda de relatórios com o Amazon Bedrock "
      "(Amazon Web Services, 2026) são provisionadas por uma configuração Terraform à parte."),

("h2", "2.3 Pipelines de integração e entrega contínuas"),
("p", "A integração e a entrega contínuas são realizadas por sete {i}pipelines{/i} do AWS CodePipeline, "
      "definidos em uma {i}stack{/i} Terraform própria, acionados por regras do Amazon EventBridge a cada "
      "{i}push{/i} no repositório AWS CodeCommit e executados pelo AWS CodeBuild a partir de "
      "{i}buildspecs{/i} versionados. Como o repositório é único, cada {i}pipeline{/i} começa verificando se "
      "o {i}push{/i} alterou os arquivos do seu artefato e, caso contrário, encerra a execução. São eles: "
      "(a) o de infraestrutura, que valida ({i}terraform fmt{/i}, {i}validate{/i} e testes da própria "
      "configuração dos {i}pipelines{/i}), planeja e, após aprovação manual, aplica o {i}bootstrap{/i} e as "
      "cinco {i}stacks{/i} na ordem do {ref:q1}, primeiro em DEV e depois em Staging; (b) os de aplicação, "
      "um por artefato conteinerizado (serviço de inferência, serviço de processamento, imagem de "
      "treinamento e as três funções Lambda, publicados em seis repositórios ECR), que executam análise "
      "estática, constroem a imagem Docker, executam os testes unitários com pytest dentro da própria "
      "imagem e a publicam no ECR com {i}tag{/i} imutável igual ao identificador do {i}commit{/i}; em "
      "seguida, implantam a nova versão em DEV, executam testes de fumaça ({i}smoke tests{/i}) contra a "
      "API e, após aprovação manual, promovem a mesma imagem, com o mesmo {i}digest{/i}, para Staging. As "
      "permissões das {i}workloads{/i} também são código: cada serviço recebe uma {i}role{/i} de privilégio "
      "mínimo via EKS Pod Identity, alterada apenas pelo {i}pipeline{/i} de infraestrutura. O serviço de "
      "inferência é executado em Python 3.12, com usuário não privilegiado no contêiner."),

("h2", "2.4 Treinamento contínuo"),
("p", "O treinamento contínuo é uma cadeia orientada a eventos, sem orquestrador central: (1) um "
      "{i}job{/i} AWS Glue, agendado semanalmente, consolida os registros de inferência em formato Delta "
      "Lake; (2) ao término bem-sucedido do {i}job{/i}, uma regra do EventBridge aciona a função "
      "etl-delta-filter, que gera arquivos Parquet incrementais na zona de treinamento do S3; (3) a "
      "criação desses arquivos aciona, por notificação do S3, a função training-launcher, que despacha "
      "um {i}Training Job{/i} do Amazon SageMaker (XGBoost) com métricas registradas no MLflow; e (4) a "
      "gravação dos artefatos do treinamento aciona a função register-best-model, que compara o F1-score "
      "medido em período posterior ao de treino ({i}out-of-time{/i}) do melhor {i}run{/i} com o da versão "
      "registrada e só registra a nova versão no {i}Model Registry{/i} se ela for superior, publicando "
      "então um evento no EventBridge. O "
      "retreinamento é, portanto, automático e periódico, condicionado à chegada de novos dados; não há "
      "acionamento por detecção de {i}drift{/i} nem por degradação de métricas em operação."),

("h2", "2.5 Inferência, ativação do modelo e escalonamento"),
("p", "O serviço de inferência é uma API REST em FastAPI no Amazon EKS. O tráfego percorre API Gateway, "
      "VPC Link e {i}Network Load Balancer{/i} (NLB) até os {i}pods{/i}, registrados diretamente como "
      "alvos por TargetGroupBinding. O modelo não é servido por {i}endpoint{/i} do SageMaker: cada "
      "{i}pod{/i} carrega, na inicialização, a versão mais recente do {i}Model Registry{/i}, que, pelo "
      "critério de promoção, é a de melhor desempenho. Como a carga ocorre apenas na inicialização, a "
      "promoção não altera {i}pods{/i} em execução; a ativação ocorre por reinicialização gradual "
      "({i}rolling restart{/i}) do {i}Deployment{/i}, executada automaticamente por um projeto do "
      "CodeBuild acionado pelo evento de nova versão, que substitui os {i}pods{/i} de forma escalonada, "
      "respeitando o "
      "{i}PodDisruptionBudget{/i}. Durante essa janela, réplicas antigas e novas podem servir versões "
      "diferentes do modelo; o tempo até a ativação completa corresponde à duração do {i}rollout{/i}, que "
      "não foi medida neste trabalho."),
("p", "O escalonamento usa dois mecanismos distintos para dois perfis de carga ({ref:q2}). O serviço de "
      "inferência, síncrono, escala pelo HPA com base na utilização de CPU, que reflete diretamente o "
      "trabalho de inferência. O serviço de processamento ({i}Process{/i}), {i}worker{/i} assíncrono que "
      "consome a fila SQS FIFO de resultados e grava no DynamoDB e no Firehose, escala pelo KEDA com base "
      "na profundidade da fila, pois sua carga é a acumulação de mensagens a consumir, desacoplada do uso "
      "de CPU no instante da chegada. Os resultados de latência da seção 3 referem-se à API de inferência "
      "e, portanto, ao HPA; o KEDA não atua sobre eles."),
("quadro", dict(id="q2", title="Configuração de escalonamento dos serviços (DEV)",
    widths=[2672, 3200, 3200],
    header=["Parâmetro", "Inferência (HPA)", "Processamento (KEDA)"],
    rows=[
        ["Perfil de carga", "Síncrono (requisição HTTP)", "Assíncrono (fila SQS FIFO)"],
        ["Métrica", "CPU média, alvo de 50%", "Profundidade da fila, 30 mensagens por réplica"],
        ["Réplicas mín./máx.", "8 / 10 (Staging: 6 / 10)", "2 / 5"],
        ["Aumento", "Imediato; até 100% ou 2 pods a cada 60 s", "Imediato; consulta à fila a cada 15 s"],
        ["Redução", "Após estabilização de 300 s", "Após 60 s de espera e 120 s de estabilização"],
    ],
    source="Fonte: elaborado pelo autor (2026).")),

("h2", "2.6 Arquitetura consolidada"),
("p", "A arquitetura integra cinco fluxos: (1) inferência síncrona (API Gateway, NLB e serviço de "
      "inferência); (2) processamento assíncrono e registro (fila SQS, serviço de processamento, "
      "DynamoDB e Firehose para o S3); (3) treinamento contínuo (Glue, funções Lambda, SageMaker e "
      "MLflow); (4) relatórios gerados com o Amazon Bedrock a partir de consultas ao Athena; e (5) IaC e "
      "CI/CD. A {ref:f1} consolida esses fluxos. O diagrama foi elaborado pela equipe do projeto; ao "
      "autor coube a infraestrutura representada (rede, EKS, filas, IaC e {i}pipelines{/i}). Na "
      "adaptação, identificadores internos foram omitidos, os rótulos foram ampliados e o fluxo da "
      "fila SQS foi corrigido conforme o código: o serviço de inferência publica os resultados e o "
      "serviço de processamento os consome."),
("figure", dict(id="f1", title="Visão geral da arquitetura da plataforma",
    source="Fonte: equipe do projeto, adaptado pelo autor (2026).")),

("h2", "2.7 Desenho experimental"),
("p", "A validação usou duas ferramentas, ambas executadas a partir da estação de trabalho do autor, no "
      "Brasil, com acesso pela internet aos {i}endpoints{/i} do API Gateway. Os testes concorrentes "
      "usaram o Locust, com 50 usuários virtuais, taxa de criação de 10 usuários por segundo e duração "
      "de 2 minutos. Cada usuário segue a política constant_throughput(1), que limita o usuário a no "
      "máximo uma requisição por segundo, mas não garante essa taxa: quando a latência se aproxima de "
      "1 s, a vazão agregada cai abaixo de 50 req/s. Não houve descarte de período de aquecimento "
      "({i}warm-up{/i}); as métricas agregadas incluem a fase inicial, e a série temporal registrada "
      "pelo Locust a cada segundo permitiu analisá-la separadamente. Foram executadas duas sessões em "
      "16/02/2026, às 22h19 e às 22h39 (horário de Brasília), com a mesma configuração e sem alteração "
      "registrada no sistema entre elas. Os testes sequenciais enviaram, em cada ambiente, 100 "
      "requisições, uma de cada vez, reutilizando a mesma conexão HTTP."),
("p", "Os relatórios do Locust não registram o ambiente-alvo. A latência mínima observada (57 ms) é "
      "incompatível com o ambiente DEV a partir do gerador de carga, cujas requisições sequenciais a esse "
      "ambiente nunca ficaram abaixo de 215 ms, e coincide com o perfil de Staging (mínimo de 73 ms; "
      "mediana de 103 ms, contra 100 ms no Locust); além disso, Staging era o alvo padrão da configuração "
      "de testes na data. Por isso, as sessões concorrentes são atribuídas ao ambiente Staging."),
("p", "O corpus de teste contém 100 {i}payloads{/i} reais de transações 3DS, percorridos em sequência "
      "circular; a requisição é considerada bem-sucedida quando retorna HTTP 200 com o campo score, e "
      "qualquer outro desfecho conta como falha. Os componentes testados foram EKS 1.32, Python 3.12, "
      "FastAPI, MLflow 3.8.1 e XGBoost 3.1.3; cada {i}pod{/i} de inferência executa dois processos "
      "Uvicorn, com reserva de 1 vCPU e 768 MiB e limite de 2 vCPU e 1,5 GiB. O número de réplicas e o "
      "tipo de nós efetivamente em execução durante os testes não foram registrados. Cada configuração "
      "foi executada uma única vez; sem repetição, os resultados descrevem as sessões observadas e não "
      "sustentam inferências causais. Os relatórios brutos do Locust e dos testes sequenciais estão "
      "preservados no repositório do projeto."),
("p", "O uso de dados reais foi autorizado formalmente pela empresa e restringiu-se aos testes "
      "executados em seus ambientes controlados. Nos {i}payloads{/i}, nome, e-mail e endereço do titular "
      "já chegam substituídos por valores de {i}hash{/i}, e o serviço de inferência utiliza apenas "
      "atributos derivados, como o BIN e os quatro últimos dígitos do cartão. Ainda assim, tais "
      "atributos constituem dados pseudonimizados e, portanto, pessoais nos termos da Lei Geral de "
      "Proteção de Dados (Brasil, 2018); por isso, nenhum {i}payload{/i} ou valor individual é "
      "reproduzido neste artigo, e os resultados são apresentados apenas de forma agregada."),

("h1", "3 RESULTADOS E DISCUSSÕES"),
("h2", "3.1 Testes de carga concorrente"),
("p", "A {ref:t1} apresenta as duas sessões concorrentes. Nas 11.910 requisições, não houve falhas, e "
      "a vazão média ficou entre 45,9 e 46,9 req/s, próxima do limite de cerca de 50 req/s imposto pela "
      "configuração de 50 usuários."),
("table", dict(id="t1", title="Resultados das sessões de carga concorrente (Staging, 50 usuários, 2 min)",
    widths=[4072, 2500, 2500],
    header=["Métrica", "Sessão 1 (22h19)", "Sessão 2 (22h39)"],
    rows=[
        ["Requisições / falhas", "5.870 / 0", "6.040 / 0"],
        ["Vazão média (req/s)", "45,9", "46,9"],
        ["Latência média (ms)", "324", "133"],
        ["P50 (ms)", "170", "100"],
        ["P90 (ms)", "810", "240"],
        ["P95 (ms)", "1.100", "330"],
        ["P99 (ms)", "1.600", "510"],
        ["Máxima (ms)", "2.059", "767"],
        ["Média nos primeiros 20 s (ms)", "586", "239"],
        ["Média nos últimos 20 s (ms)", "145", "98"],
    ],
    source="Fonte: dados da pesquisa (2026).")),
("p", "A diferença entre as sessões concentra-se no início. Na sessão 1, a latência média por janela "
      "caiu continuamente, de 586 ms nos primeiros 20 s para 145 ms nos últimos 20 s, sem estabilizar "
      "dentro dos 2 minutos; na sessão 2, já começou mais baixa (239 ms) e estabilizou em torno de "
      "100 ms após cerca de 60 s. As métricas agregadas da sessão 1 são, assim, dominadas pela fase de "
      "aquecimento. Como não houve alteração registrada no sistema entre as sessões, a diferença não "
      "pode ser atribuída a nenhuma intervenção; hipóteses plausíveis, como o estabelecimento inicial de "
      "conexões, o preenchimento de {i}caches{/i} e o estado das réplicas, não foram medidas. Esses "
      "resultados são evidência do comportamento nas sessões testadas, e não da disponibilidade contínua "
      "do serviço."),

("h2", "3.2 Testes sequenciais em DEV e Staging"),
("p", "A {ref:t2} compara os testes sequenciais nos dois ambientes, executados com o mesmo "
      "procedimento e o mesmo corpus. Nenhum teste apresentou falhas."),
("table", dict(id="t2", title="Latências dos testes sequenciais por ambiente (100 requisições)",
    widths=[4072, 2500, 2500],
    header=["Métrica", "DEV (us-east-1)", "Staging (sa-east-1)"],
    rows=[
        ["Latência média (ms)", "287", "103"],
        ["Mediana (ms)", "279", "103"],
        ["Mínima (ms)", "215", "72,6"],
        ["P90 (ms)", "328", "114,5"],
        ["P95 (ms)", "345", "123,9"],
        ["Máxima (ms)", "423", "157,8"],
    ],
    source="Fonte: dados da pesquisa (2026).")),
("p", "A latência em Staging foi, em média, 184 ms menor. A diferença entre as mínimas (cerca de 140 ms) "
      "é compatível com a maior distância de rede entre o gerador de carga, no Brasil, e a região "
      "us-east-1; contudo, os ambientes também diferem em configuração (número mínimo de réplicas, versões "
      "implantadas e volume de dados), e a comparação não foi isolada experimentalmente. A localização "
      "geográfica é, portanto, uma hipótese plausível, e não uma causa estabelecida."),

("h2", "3.3 Confronto com os critérios de aceitação"),
("p", "A {ref:t3} confronta os resultados das sessões concorrentes com os critérios definidos na seção "
      "1.1."),
("table", dict(id="t3", title="Resultados das sessões concorrentes frente aos critérios de aceitação",
    widths=[1900, 1600, 1500, 1500, 2572],
    header=["Critério", "Meta", "Sessão 1", "Sessão 2", "Situação"],
    rows=[
        ["Taxa de falhas", "< 1%", "0%", "0%", "Atendido nas sessões"],
        ["Latência P95", "< 500 ms", "1.100 ms", "330 ms", "Atendido só na sessão 2"],
        ["Latência P99", "< 1.000 ms", "1.600 ms", "510 ms", "Atendido só na sessão 2"],
        ["Vazão", "≥ 100 req/s", "45,9 req/s", "46,9 req/s", "Não validado"],
    ],
    note="Nota: a configuração de 50 usuários limita a vazão a cerca de 50 req/s; o cenário com 100 "
         "usuários não foi executado, e os resultados não devem ser extrapolados linearmente.",
    source="Fonte: dados da pesquisa (2026).")),
("p", "O requisito de vazão de 100 req/s não foi demonstrado e permanece não validado. Os critérios de "
      "latência foram atendidos apenas na segunda sessão, com o sistema já aquecido, o que indica que o "
      "atendimento depende do estado do serviço e precisa ser confirmado em execuções repetidas."),

("h2", "3.4 Discussão"),
("p", "{b}Separação entre CI/CD e CT.{/b} A principal decisão arquitetural foi manter a entrega de "
      "código e a entrega de modelos em trilhas independentes: uma nova versão do modelo é promovida sem "
      "alteração de código, e uma nova versão do serviço é implantada sem retreinamento. A promoção "
      "condicionada à métrica no {i}Model Registry{/i} funciona como portão de governança. Essa separação "
      "foi demonstrada em implementação e configuração; a eficácia do ciclo de CT ao longo do tempo, como "
      "a frequência de promoções e o ganho preditivo obtido, não foi medida."),
("p", "{b}Escalonamento.{/b} O HPA e o KEDA foram configurados e implantados, mas os testes aplicaram "
      "carga estável, sem variação brusca; o comportamento dinâmico de ambos sob picos, assim como o "
      "número de réplicas durante os testes, não foi observado. Não se afirma, portanto, que o "
      "escalonamento tenha sido validado sob demanda variável."),
("p", "{b}Variabilidade da latência.{/b} A distância entre P50 (100 ms) e P99 (510 ms) na sessão 2 pode "
      "decorrer de consultas ao DynamoDB para clientes com histórico extenso, do carregamento do modelo em "
      "réplicas recém-criadas e da coleta de lixo do Python. Essas causas não foram medidas isoladamente "
      "e permanecem como hipóteses."),
("p", "{b}Ambiente de teste.{/b} A diferença entre DEV e Staging, somada ao efeito de aquecimento, "
      "mostra que valores absolutos de latência não se transferem entre ambientes nem entre sessões: "
      "testes de desempenho devem ser executados no ambiente de destino, com carga representativa, "
      "repetições e registro do estado da infraestrutura."),

("h1", "4 CONCLUSÃO"),
("p", "Este trabalho investigou como integrar de forma automatizada o ciclo de vida de modelos de ML a "
      "{i}pipelines{/i} DevOps, em uma plataforma de detecção de fraude construída sobre serviços "
      "gerenciados da AWS e validada nos ambientes de desenvolvimento e homologação. Os quatro primeiros "
      "objetivos específicos foram atendidos em implementação: as camadas de DevOps e MLOps foram "
      "separadas; a infraestrutura foi codificada em 15 módulos Terraform e cinco {i}stacks{/i}, com "
      "paridade entre ambientes; os {i}pipelines{/i} de CI/CD e o ciclo de CT foram implementados; e o "
      "MLflow tornou-se a referência da versão do modelo em uso. O quinto objetivo foi atendido em parte: "
      "o escalonamento foi configurado e implantado, e o desempenho foi avaliado em sessões delimitadas, "
      "sem falhas e com os critérios de latência atendidos na segunda sessão; a vazão de 100 req/s e o "
      "comportamento sob picos, contudo, não foram validados."),
("p", "Como contribuições, destacam-se: um padrão arquitetural em que CI/CD e CT são mecanismos "
      "independentes e conectados apenas pelo registro de modelos; uma referência de implementação "
      "MLOps em nuvem, com IaC modular; o uso complementar de HPA e KEDA para cargas síncronas e "
      "assíncronas; e a constatação de que a análise da série temporal dos testes revela efeitos de "
      "aquecimento ocultos nas métricas agregadas."),
("p", "O trabalho tem limitações. Cada cenário foi executado uma única vez, sem repetição estatística; o "
      "ambiente das sessões concorrentes foi inferido, e não registrado; o número de réplicas durante os "
      "testes não foi capturado; a vazão-alvo e o comportamento do escalonamento sob picos não foram "
      "testados; o retreinamento não é acionado por {i}drift{/i}; o tempo de ativação de uma nova versão "
      "do modelo não foi medido; e a validação limitou-se a ambientes de desenvolvimento e homologação de "
      "um único provedor de nuvem, o que restringe a generalização dos resultados."),
("p", "Como trabalhos futuros, propõem-se: repetir os testes com 100 ou mais usuários e com cenários de "
      "pico, registrando réplicas e nós; medir o tempo de ativação de novas versões do modelo; acionar o "
      "retreinamento pela detecção automática de {i}drift{/i}; adotar liberação gradual ({i}canary "
      "release{/i}) de modelos; comparar quantitativamente HPA e KEDA; instrumentar o serviço com "
      "rastreamento distribuído para explicar a variabilidade do P99; e avaliar a plataforma em "
      "produção, com monitoramento longitudinal de disponibilidade."),
]

# ---------------------------------------------------------------------------
# Referências (ordem alfabética; título/periódico em negrito)
# ---------------------------------------------------------------------------
REFS = [
 "AMAZON WEB SERVICES. {b}Amazon Bedrock{/b}: user guide. [S. l.]: AWS, 2026. Disponível em: https://docs.aws.amazon.com/bedrock/. Acesso em: 12 nov. 2026.",
 "BRASIL. {b}Lei nº 13.709, de 14 de agosto de 2018{/b}. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 12 nov. 2026.",
 "BRECK, Eric et al. The ML test score: a rubric for ML production readiness and technical debt reduction. In: IEEE INTERNATIONAL CONFERENCE ON BIG DATA, 2017, Boston. {b}Proceedings{/b} [...]. Piscataway: IEEE, 2017. p. 1123-1132.",
 "BRIKMAN, Yevgeniy. {b}Terraform{/b}: up & running: writing infrastructure as code. 2. ed. Sebastopol: O'Reilly Media, 2019.",
 "BURNS, Brendan et al. {b}Kubernetes{/b}: up and running: dive into the future of infrastructure. 3. ed. Sebastopol: O'Reilly Media, 2022.",
 "FOWLER, Martin. {b}Continuous integration{/b}. [S. l.], 2006. Disponível em: https://martinfowler.com/articles/continuousIntegration.html. Acesso em: 12 nov. 2026.",
 "GAMA, João et al. A survey on concept drift adaptation. {b}ACM Computing Surveys{/b}, New York, v. 46, n. 4, p. 1-37, 2014.",
 "GOOGLE CLOUD. {b}MLOps{/b}: continuous delivery and automation pipelines in machine learning. [S. l.], 2023. Disponível em: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning. Acesso em: 12 nov. 2026.",
 "HUMBLE, Jez; FARLEY, David. {b}Continuous delivery{/b}: reliable software releases through build, test, and deployment automation. Boston: Addison-Wesley, 2010.",
 "KEDA. {b}KEDA documentation{/b}: Kubernetes event-driven autoscaling. [S. l.], 2026. Disponível em: https://keda.sh/docs/. Acesso em: 12 nov. 2026.",
 "KIM, Gene et al. {b}The DevOps handbook{/b}: how to create world-class agility, reliability, and security in technology organizations. Portland: IT Revolution Press, 2016.",
 "KREUZBERGER, Dominik; KÜHL, Niklas; HIRSCHL, Sebastian. Machine learning operations (MLOps): overview, definition, and architecture. {b}IEEE Access{/b}, [S. l.], v. 11, p. 31866-31879, 2023.",
 "MÄKINEN, Sasu et al. Who needs MLOps: what data scientists seek to accomplish and how can MLOps help? In: IEEE/ACM WORKSHOP ON AI ENGINEERING - SOFTWARE ENGINEERING FOR AI (WAIN), 1., 2021, Madrid. {b}Proceedings{/b} [...]. Piscataway: IEEE, 2021. p. 109-112.",
 "MORRIS, Kief. {b}Infrastructure as code{/b}: dynamic systems for the cloud age. 2. ed. Sebastopol: O'Reilly Media, 2020.",
 "SCULLEY, D. et al. Hidden technical debt in machine learning systems. In: CONFERENCE ON NEURAL INFORMATION PROCESSING SYSTEMS, 28., 2015, Montreal. {b}Advances in Neural Information Processing Systems 28{/b}. Red Hook: Curran Associates, 2015. p. 2503-2511.",
 "TREVEIL, Mark et al. {b}Introducing MLOps{/b}: how to scale machine learning in the enterprise. Sebastopol: O'Reilly Media, 2020.",
 "ZAHARIA, Matei et al. Accelerating the machine learning lifecycle with MLflow. {b}Bulletin of the IEEE Computer Society Technical Committee on Data Engineering{/b}, [S. l.], v. 41, n. 4, p. 39-45, 2018.",
]

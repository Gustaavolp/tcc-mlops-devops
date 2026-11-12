# Guia de Apresentação — TCC I (Apresentação de Andamento)

**Duração alvo: 10 minutos  ·  17 slides  ·  Arquivo: `Apresentacao_TCC1_MeioAno_Gustavo.pptx`**

> ⚠️ Os 4 diagramas técnicos originais do projeto (antes anexos fora do tempo) agora fazem parte do fluxo cronometrado dos 10 minutos, intercalados nos pontos temáticos correspondentes (após Arquitetura, após Pipelines, após Autoscaling). Para abrir espaço, as falas dos slides 3, 4, 5, 6, 15 e 16 foram enxugadas ainda mais. A versão anterior (13 slides + 4 anexos fora do tempo) está preservada em `backup_10min_anexos_apendice_2026-07-06/`.
>
> **A folga antes do limite de 10 minutos caiu de ~50s para ~20s.** Não há mais espaço de sobra — ensaie com cronômetro real antes da apresentação.

## Como usar este guia

Isto não é um script para decorar palavra por palavra — é um roteiro de pontos-chave. Fale com suas próprias palavras; o guia existe para você não esquecer o essencial e não perder tempo em detalhes secundários. Os tempos são cumulativos e **saem muito apertados** — com os 4 diagramas agora dentro do tempo, praticamente não há folga. Ensaie com cronômetro antes; se estiver estourando, corte pelos pontos indicados nos checkpoints, não improvise cortes no meio de um slide.

**Regra de ouro nº 1 (feedback do orientador):** não leia o slide. Ele já mostra a informação — sua fala deve *complementar*, não repetir. Isso vale em dobro para os 4 slides de diagrama: são só reforço visual, uma frase basta, não descreva cada ícone.

**Regra de ouro nº 2 (feedback do orientador):** em qualquer momento que mencionar números de latência/throughput dos testes, diga a palavra **"preliminar"** em voz alta. Isso já está escrito no slide 14, mas reforce oralmente — é o ponto mais importante do feedback recebido.

---

## Checklist antes de começar
- [ ] Cronômetro visível (celular ou relógio) — ensaiar pelo menos 2x com cronômetro real; com os diagramas integrados, o ritmo é mais apertado do que antes.
- [ ] Saber de cor os 3 números centrais: **93% recall**, **P95 1.100ms → 330ms (−70%)**, **10.000 req/s (SLA) vs. ~100 RPS (testado)**.
- [ ] Nos 4 slides de diagrama (8, 9, 11, 13): treinar a frase única de cada um — não é para explicar o diagrama do zero, só confirmar o que já foi dito.
- [ ] Ter lido a seção "Perguntas prováveis" no fim deste guia pelo menos uma vez.
- [ ] Ter internalizado que, se a banca fizer uma pergunta durante a fala, isso consome tempo do seu orçamento de 10 minutos — responda de forma direta e curta.

---

## Slide 1 — Capa  `alvo: 0:00–0:15`
Só se apresente e apresente o tema. Não precisa ler o subtítulo do slide.

> "Boa tarde. Meu nome é Gustavo Liebl Pereira, e esta é a apresentação de andamento do meu TCC I, orientado pelo professor Marcelo Semmer, sobre integração de MLOps em pipelines DevOps."

**Transição:** "Vou direto à agenda, para aproveitar bem os 10 minutos."

---

## Slide 2 — Agenda  `alvo: 0:15–0:35`
Não leia os itens um por um. Uma frase só, agrupando em blocos.

> "A apresentação cobre quatro blocos: o problema e o contexto real do projeto; a metodologia em quatro fases; a arquitetura e os pipelines implementados — com os diagramas técnicos originais do projeto como referência; e o estado atual com os próximos passos. Os resultados que mostro são um preview — a validação completa fica para o TCC II."

**Transição:** "Vamos direto ao problema de pesquisa."

---

## Slide 3 — Problema de Pesquisa e Contexto do Cliente  `alvo: 0:35–1:40`
Vá rápido nos dois quadros (Data Science vs. Engenharia); gaste a maior parte do tempo no contexto real, que dá força de fonte primária ao trabalho.

> "Do lado de Data Science, falta API de servimento e pipeline de retreinamento; do lado de Engenharia, falta deploy automatizado e governança. A literatura confirma: Gartner estima que 85% dos projetos de ML nunca chegam à produção, e Sculley et al. mostram que a maior parte do código de um sistema de ML real é infraestrutura, não o modelo."

> "Este trabalho nasce de uma demanda real: uma plataforma de detecção de fraude 3DS de uma empresa de grande porte, com MVP validado em 93% de recall e SLA rigoroso — p95 abaixo de 500ms, 99,9% de disponibilidade, 10.000 requisições por segundo, LGPD. Minha autoria foi a camada de Engenharia DevOps — Terraform, EKS, CI/CD; o modelo de Machine Learning foi de outra frente, de Data Science."

**Transição:** "Com esse contexto, a pergunta de pesquisa e os objetivos ficam mais concretos."

---

## Slide 4 — Pergunta de Pesquisa e Objetivos  `alvo: 1:40–2:15`
Leia a pergunta de pesquisa (vale ler literalmente uma vez). Os objetivos, **não leia** — cite o padrão comum entre eles.

> "A pergunta de pesquisa é: como integrar de forma eficiente e automatizada o ciclo de vida de MLOps em pipelines DevOps, garantindo entrega contínua em produção? Os quatro objetivos cobrem da arquitetura de integração à validação experimental do escalonamento, sempre em um projeto prático real em nuvem."

**Transição:** "Para isso, segui uma metodologia em quatro fases."

---

## Slide 5 — Metodologia — Visão Geral  `alvo: 2:15–2:50`
Aponte o fluxo visual, não leia os cards em detalhe.

> "É uma pesquisa aplicada, experimental e construtiva: eu mesmo projetei, implementei e validei a plataforma — o sistema é, ao mesmo tempo, o artefato e o instrumento de validação. Quatro fases: levantamento bibliográfico, infraestrutura como código, pipelines de CI/CD e treinamento contínuo, e validação experimental."

**Transição:** "Rapidamente, a Fase 1."

---

## Slide 6 — Fase 1: Levantamento Bibliográfico  `alvo: 2:50–3:10`
Não leia as 5 lacunas — resuma em uma frase única.

> "O levantamento em IEEE Xplore, ACM e Google Scholar identificou cinco lacunas — da separação entre CI/CD e treinamento contínuo ao autoscaling orientado a eventos — que moldaram diretamente as escolhas de arquitetura a seguir."

**Transição:** "Essa é a arquitetura que elas moldaram."

---

## Slide 7 — Arquitetura da Plataforma  `alvo: 3:10–4:10`
Este é o slide mais denso do bloco central — vá camada por camada, sem ler as setas literalmente, ritmo firme.

> "Quatro trilhas. Inferência em tempo real: a transação 3DS chega via API Gateway, passa por um NLB e vai direto para os pods do serviço de inferência em FastAPI — sem Application Load Balancer no caminho — que consulta o DynamoDB como feature store e retorna o score. Processamento assíncrono: o resultado vai para uma fila SQS FIFO, consumida por um worker que escala via KEDA, e segue via Kinesis Firehose para o data lake em S3. Treinamento contínuo: toda semana um job Glue processa os logs, dispara Lambdas que treinam um novo modelo no SageMaker e o registram no MLflow, só promovendo se ele superar o modelo atual. E por trás de tudo, Terraform 1.14 provisiona a infraestrutura em 5 stacks e 15 módulos, e o AWS CodeBuild cuida do CI/CD."

**Transição:** "Antes de seguir, o diagrama técnico original do projeto confirma essa mesma arquitetura."

---

## Slide 8 — Diagrama de Referência: Infraestrutura — Visão Geral  `alvo: 4:10–4:30`
Diagrama original do projeto (imagem não alterada) — é só confirmação visual, uma frase basta. Não descreva cada ícone.

> "Este é o diagrama de infraestrutura documentado pela própria equipe do projeto — confirma, com uma fonte independente, a mesma cadeia que acabei de descrever: API Gateway, VPC Link, NLB, sem ALB, e a trilha completa de treinamento contínuo até o MLflow."

**Transição:** "E o fluxo síncrono de inferência, em detalhe:"

---

## Slide 9 — Diagrama de Referência: Fluxo 1 (Inference Síncrono)  `alvo: 4:30–4:50`
Mesma lógica: uma frase, sem se aprofundar nos 5 passos internos do pipeline.

> "Aqui está o pipeline interno do serviço de inferência, passo a passo: normalização, extração e enriquecimento de features, chamada ao modelo, e construção da resposta — exatamente o fluxo que descrevi na arquitetura."

**Transição:** "Voltando aos pipelines de código: CI/CD e treinamento contínuo."

---

## Slide 10 — Pipelines CI/CD + CT  `alvo: 4:50–5:35`
Reforce a separação entre as duas trilhas — é a "contribuição central" do slide.

> "A trilha de CI/CD é direta: commit, build da imagem, push para o ECR, deploy no EKS via AWS CodeBuild. A trilha de treinamento contínuo é inteiramente serverless: Glue, EventBridge e três funções Lambda que treinam, avaliam por F1-score e promovem o modelo automaticamente, sem intervenção manual. O ponto central é que essas duas trilhas são desacopladas — código e ciclo de vida do modelo evoluem de forma independente, o que era justamente uma lacuna identificada na literatura."

**Transição:** "Esse fluxo de treinamento contínuo também está documentado no diagrama original."

---

## Slide 11 — Diagrama de Referência: Fluxo 3 (MLOps)  `alvo: 5:35–5:55`
Uma frase, confirmando a cadeia event-driven já descrita.

> "E este é o fluxo de MLOps documentado pela equipe, em quatro etapas — ETL, engenharia de features, treinamento no SageMaker e registro condicional no MLflow — a mesma cadeia event-driven que acabei de apresentar."

**Transição:** "Agora, como os dois serviços escalam."

---

## Slide 12 — Autoscaling: HPA (Inferência) + KEDA (Process)  `alvo: 5:55–6:45`
**Ponto historicamente corrigido — não confunda os dois mecanismos.** Fale devagar, é o ponto mais provável de gerar pergunta da banca.

> "Dois serviços, dois mecanismos de escalonamento, e isso é intencional. O serviço de Inferência — a API síncrona que responde o score — escala por um HPA tradicional baseado em CPU, de 8 a 10 réplicas, porque a carga dele é correlacionada ao uso de CPU. Já o serviço Process — o worker assíncrono que consome a fila de resultados — escala via KEDA, baseado na profundidade da fila SQS FIFO, de 2 a 5 réplicas, porque a carga dele chega em rajadas, desacopladas de CPU. Não é 'KEDA para tudo' — é o mecanismo certo para o padrão de carga de cada serviço."

**Transição:** "O fluxo assíncrono do Process também está documentado no diagrama original."

---

## Slide 13 — Diagrama de Referência: Fluxo 2 (Process Assíncrono)  `alvo: 6:45–7:05`
Uma frase, ligando de volta ao KEDA que acabou de ser explicado.

> "E este mostra o fluxo assíncrono do Process: a fila SQS FIFO alimentando o serviço no EKS, que atualiza o DynamoDB e persiste os logs no S3 — o mesmo serviço que o KEDA escala."

**Transição:** "Com arquitetura, pipelines e escalonamento cobertos, a Fase 4 foi validar tudo isso experimentalmente."

---

## Slide 14 — Resultados Preliminares  `alvo: 7:05–8:10`
O clímax da apresentação — fale com mais ênfase, mas sem se alongar no método (uma frase basta). Diga **"preliminar"** aqui, é obrigatório.

> "Usei Locust com 100 payloads reais de transações 3DS, no endpoint de autorização, em DEV e Staging. Durante os testes sequenciais em DEV, sem HTTP keepalive, observei picos isolados e recorrentes — uma requisição levou 5,2 segundos, outra 2,6 segundos, no meio de requisições normais de 180ms. O diagnóstico: sem keepalive, o NLB encerra a conexão TCP por timeout, e cada nova requisição reconecta toda a cadeia de rede, o que adiciona de 1 a 4 segundos. Habilitando o keepalive, sem mudar infraestrutura, modelo ou algoritmo, o p95 caiu de 1.100 milissegundos para 330 — uma redução de 70%. Repito: isso é um resultado **preliminar**, do ambiente DEV; o SLA contratado de 10.000 requisições por segundo ainda não foi validado — fica para o TCC II."

**Transição:** "Diante disso, esse é o estado atual e o que vem a seguir."

---

## Slide 15 — Estado Atual & Trabalhos Futuros  `alvo: 8:10–8:50`
Rápido na tabela de status (uma frase), um pouco mais de tempo nos próximos passos.

> "Dos quatro objetivos específicos, três estão totalmente implementados; a governança e o escalonamento por eventos estão validados parcialmente — falta o teste sob carga de spike. Para o TCC II: validar experimentalmente as metas de 100 RPS e do SLA de 10.000 requisições por segundo; evoluir a promoção de modelos para um canary release; e avançar para detecção automática de concept drift."

**Transição:** "Fechando, a conclusão parcial deste momento do trabalho."

---

## Slide 16 — Conclusão Parcial  `alvo: 8:50–9:25`
Feche com força — repita o achado central mais uma vez, é o que fica na memória da banca.

> "Os resultados até aqui indicam que integrar MLOps a pipelines DevOps de forma eficiente exige separação arquitetural entre CI/CD e treinamento contínuo, automação serverless para o ciclo de vida do modelo, infraestrutura modularizada por domínio, e testes de carga com payloads reais como parte do processo — não uma etapa opcional. O achado preliminar mais relevante segue sendo a otimização de HTTP keepalive, com redução de 70% no p95, sem qualquer mudança de infraestrutura, modelo ou algoritmo. Para o TCC II, o foco é consolidar essa validação rumo ao SLA real de 10.000 requisições por segundo, e finalizar a redação do artigo."

**Transição:** "Muito obrigado."

---

## Slide 17 — Obrigado  `alvo: 9:25–9:40`
> "Muito obrigado pela atenção. Fico à disposição para perguntas."

*(Isso encerra a fala em ~9:40, deixando apenas ~20 segundos de folga antes do limite de 10 minutos. Não é espaço para respirar entre slides — é uma margem de segurança para imprevistos. Ensaie até esse tempo fechar com sobra real.)*

---

## Perguntas prováveis do orientador/banca — e como responder

**"Por que só ~100 RPS testados se o SLA é de 10.000 req/s?"**
> "Essa é exatamente a delimitação de escopo da TCC I: os 100 RPS são uma meta interna de validação, viável no tempo e infraestrutura desta etapa. O SLA de 10.000 req/s é o alvo contratual de produção, e a validação dessa escala fica para a TCC II — envolve testes de carga maiores e possivelmente ajustes de infraestrutura."

**"Qual foi exatamente sua contribuição, já que o modelo foi feito por outra pessoa?"**
> "Minha autoria é a camada de DevOps/Infraestrutura: todo o Terraform, a arquitetura Kubernetes, os pipelines de CI/CD e CT, e o monitoramento. O modelo de Machine Learning — as features e o algoritmo — foi construído por outra frente da equipe, de Data Science. Isso está documentado na definição de papéis do projeto, e é justamente essa separação de responsabilidades que o TCC discute como boa prática de MLOps."

**"Existe um Application Load Balancer na arquitetura?"**
> "Não, na configuração atual. A cadeia é API Gateway, VPC Link, NLB, direto para os pods via TargetGroupBinding. Não há ALB no caminho de inferência — e os diagramas técnicos originais do projeto, que mostrei nos slides 8 e 9, confirmam exatamente essa mesma cadeia."

**"Por que a Inferência usa HPA por CPU e o Process usa KEDA por fila, e não os dois pelo mesmo mecanismo?"**
> "Porque o padrão de carga é diferente. A Inferência responde de forma síncrona e tem uso de CPU proporcional ao tráfego. O Process consome uma fila de forma assíncrona e em rajadas — a profundidade da fila é um sinal mais direto de demanda real do que a CPU nesse caso."

**"Os dados e documentos internos do cliente podem ser citados no artigo final?"**
> "Estão classificados como restritos. Qualquer citação literal depende de autorização formal da empresa — algo que pretendo buscar antes da versão final do artigo, ou, alternativamente, manter a descrição em termos gerais e anonimizados. Os diagramas técnicos que apresentei já são usados diretamente com essa autorização."

**"O que exatamente mudou entre TCC I e TCC II?"**
> "Na TCC I entrego a arquitetura completa implementada e um achado preliminar de latência. Na TCC II, consolido a validação experimental completa — incluindo as metas reais de throughput, o comportamento sob picos de carga, e a análise estatística nos dois ambientes — além de finalizar a redação e a conclusão do artigo."

**"Por que a apresentação tem slides de diagrama intercalados com os slides normais?"**
> "São os diagramas técnicos originais do projeto, documentados pela própria equipe — inseri-los logo após cada bloco correspondente (arquitetura, pipelines, autoscaling) permite confirmar visualmente, com uma fonte independente, o que acabei de descrever, sem depender só da minha representação da arquitetura."

---

## Resumo de tempo (checkpoints)

Com os 4 diagramas agora dentro dos 10 minutos, a margem de manobra é mínima — trate estes checkpoints como sinais de alerta, não como pontos opcionais.

| Checkpoint | Tempo alvo | Se estiver atrasado... |
|---|---|---|
| Fim do slide 4 (Objetivos) | ~2:15 | Encurte ainda mais o slide 3 — corte a citação de Sculley e vá direto ao contexto do cliente |
| Fim do slide 9 (Diagrama Fluxo 1) | ~4:50 | Nos slides 8 e 9, reduza a uma frase cada — não pare para apontar detalhes do diagrama |
| Fim do slide 14 (Resultados) | ~8:10 | Encurte o slide 15 — cite só 1 próximo passo (throughput), não os 3 |
| Fim do slide 16 (Conclusão) | ~9:25 | Nunca corte a conclusão nem o achado do keepalive — é o fechamento que fica na memória da banca |

**Se, mesmo assim, o ensaio mostrar que 10 minutos não são suficientes:** os candidatos a corte adicional, em ordem de prioridade, são: (1) reduzir os slides 8, 9, 11 e 13 (diagramas) a uma frase ainda mais curta cada — por exemplo, "o diagrama original do cliente confirma essa arquitetura" sem repetir os detalhes; (2) resumir o slide 6 (Fase 1) a uma única frase; (3) cortar o segundo próximo passo do slide 15. Não corte o slide 12 (HPA vs. KEDA) nem o slide 14 (achado do keepalive) — são o núcleo técnico e empírico do trabalho.

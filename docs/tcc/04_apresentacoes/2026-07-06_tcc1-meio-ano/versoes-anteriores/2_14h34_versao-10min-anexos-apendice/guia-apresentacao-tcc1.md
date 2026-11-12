# Guia de Apresentação — TCC I (Apresentação de Andamento)

**Duração alvo: 10 minutos  ·  13 slides + 4 anexos  ·  Arquivo: `Apresentacao_TCC1_MeioAno_Gustavo.pptx`**

> ⚠️ O cronograma foi reduzido de 15 para 10 minutos. Este guia substitui a versão anterior (de 17 slides / 15 min, preservada em `backup_15min_2026-07-06/`). Três pares de slides foram fundidos (Problema+Contexto do Cliente; Setup+Preview de Resultados; Estado Atual+Trabalhos Futuros) e o texto de cada slide foi enxugado — isso reduz o volume falado em ~35%, compensando a redução de tempo.

## Como usar este guia

Isto não é um script para decorar palavra por palavra — é um roteiro de pontos-chave. Fale com suas próprias palavras; o guia existe para você não esquecer o essencial e não perder tempo em detalhes secundários. Os tempos são cumulativos e **já saem apertados** — em 10 minutos não há espaço de sobra como havia na versão de 15. Ensaie com cronômetro antes; se estiver estourando, corte pelos pontos indicados nos checkpoints, não improvise cortes no meio de um slide.

**Regra de ouro nº 1 (feedback do orientador):** não leia o slide. Ele já mostra a informação — sua fala deve *complementar*, não repetir. Com menos tempo ainda, isso é mais crítico: ler o slide em voz alta é a forma mais fácil de estourar o tempo.

**Regra de ouro nº 2 (feedback do orientador):** em qualquer momento que mencionar números de latência/throughput dos testes, diga a palavra **"preliminar"** em voz alta. Isso já está escrito no slide 10, mas reforce oralmente — é o ponto mais importante do feedback recebido, e continua valendo integralmente na versão de 10 minutos.

---

## Checklist antes de começar
- [ ] Cronômetro visível (celular ou relógio) — ensaiar pelo menos 1x com cronômetro real; 10 minutos é um ritmo mais rápido do que o natural, exige ensaio.
- [ ] Saber de cor os 3 números centrais: **93% recall**, **P95 1.100ms → 330ms (−70%)**, **10.000 req/s (SLA) vs. ~100 RPS (testado)**.
- [ ] Ter lido a seção "Perguntas prováveis" no fim deste guia pelo menos uma vez.
- [ ] Ter internalizado que, se a banca fizer uma pergunta durante a fala, isso consome tempo do seu orçamento de 10 minutos — responda de forma direta e curta.

---

## Slide 1 — Capa  `alvo: 0:00–0:15`
Só se apresente e apresente o tema. Não precisa ler o subtítulo do slide.

> "Boa tarde. Meu nome é Gustavo Liebl Pereira, e esta é a apresentação de andamento do meu TCC I, orientado pelo professor Marcelo Semmer, sobre integração de MLOps em pipelines DevOps."

**Transição:** "Vou direto à agenda, para aproveitar bem os 10 minutos."

---

## Slide 2 — Agenda  `alvo: 0:15–0:35`
Não leia os 10 itens um por um. Uma frase só, agrupando em blocos.

> "A apresentação cobre quatro blocos: o problema e o contexto real do projeto; a metodologia em quatro fases; a arquitetura e os pipelines implementados; e o estado atual com os próximos passos. Os resultados que mostro são um preview — a validação completa fica para o TCC II."

**Transição:** "Vamos direto ao problema de pesquisa."

---

## Slide 3 — Problema de Pesquisa e Contexto do Cliente  `alvo: 0:35–1:50`
Este slide fundiu dois temas — vá rápido nos dois quadros (Data Science vs. Engenharia), gaste a maior parte do tempo no bloco de baixo (contexto real), que é o que dá força de fonte primária ao trabalho.

> "Do lado de Data Science, o modelo funciona bem no notebook, mas falta API de servimento, versionamento, pipeline de retreinamento. Do lado de Engenharia, falta deploy automatizado, detecção de drift, governança. A literatura confirma isso: Gartner estima que 85% dos projetos de ML nunca chegam à produção, e Sculley et al. já apontavam que a maior parte do código de um sistema de ML real é infraestrutura, não o modelo em si."

Sem citar o nome do cliente (a apresentação já está anonimizada), conecte com o caso real e feche com a delimitação de escopo — isso precisa ficar muito claro:

> "Este trabalho nasce de uma demanda real e documentada: uma plataforma de detecção de fraude 3DS de uma empresa de grande porte, com um MVP já validado em 93% de recall, e um SLA contratual rigoroso — p95 abaixo de 500ms, 99,9% de disponibilidade, 10.000 requisições por segundo, LGPD. É fundamental deixar claro o escopo da minha autoria: atuei como Engenheiro DevOps — Terraform, EKS, CI/CD. O modelo de Machine Learning em si foi de outra frente da equipe, de Data Science."

**Transição:** "Com esse contexto, a pergunta de pesquisa e os objetivos ficam mais concretos."

---

## Slide 4 — Pergunta de Pesquisa e Objetivos  `alvo: 1:50–2:35`
Leia a pergunta de pesquisa (ela é densa, vale ler literalmente uma vez). Os 4 objetivos, **não leia** — cite o padrão comum entre eles em uma frase.

> "A pergunta de pesquisa que guia este trabalho é: como integrar de forma eficiente, escalável e automatizada o ciclo de vida de MLOps em pipelines DevOps, garantindo entrega contínua e governança em produção? Os quatro objetivos específicos cobrem desde a arquitetura de integração até a validação experimental do escalonamento — todos voltados a demonstrar, num projeto prático em nuvem, as boas práticas e os desafios reais dessa integração."

**Transição:** "Para isso, segui uma metodologia em quatro fases."

---

## Slide 5 — Metodologia — Visão Geral  `alvo: 2:35–3:15`
Aponte o fluxo visual, não leia os cards em detalhe.

> "É uma pesquisa aplicada, experimental e construtiva: eu mesmo projetei, implementei e validei a plataforma — o sistema construído é, ao mesmo tempo, o artefato de pesquisa e o instrumento de validação. Quatro fases sequenciais: levantamento bibliográfico, infraestrutura como código, pipelines de CI/CD e treinamento contínuo, e validação experimental."

**Transição:** "Rapidamente, a Fase 1."

---

## Slide 6 — Fase 1: Levantamento Bibliográfico  `alvo: 3:15–3:45`
Não leia as 5 lacunas com citações — resuma a ideia central de cada uma em poucas palavras.

> "Levantamento em IEEE Xplore, ACM e Google Scholar, priorizando trabalhos com implementação prática. Cinco lacunas guiaram a arquitetura: separação entre CI/CD e treinamento contínuo, comparação entre MLflow gerenciado e self-hosted, autoscaling orientado a eventos para cargas de ML, impacto de otimizações de rede na inferência, e modularização de IaC por domínio. Essas lacunas aparecem resolvidas na arquitetura a seguir."

**Transição:** "Essa é a arquitetura que elas moldaram."

---

## Slide 7 — Arquitetura da Plataforma  `alvo: 3:45–4:45`
Este é o slide mais denso — vá camada por camada, sem ler as setas literalmente, mantendo ritmo firme (é o slide onde é mais fácil perder tempo).

> "Quatro trilhas. Inferência em tempo real: a transação 3DS chega via API Gateway, passa por um NLB e vai direto para os pods do serviço de inferência em FastAPI — sem Application Load Balancer no caminho — que consulta o DynamoDB como feature store e retorna o score. Processamento assíncrono: o resultado vai para uma fila SQS FIFO, consumida por um worker que escala via KEDA, e segue via Kinesis Firehose para o data lake em S3. Treinamento contínuo: toda semana um job Glue processa os logs, dispara Lambdas que treinam um novo modelo no SageMaker e o registram no MLflow, só promovendo se ele superar o modelo atual. E por trás de tudo, Terraform 1.14 provisiona a infraestrutura em 5 stacks e 15 módulos, e o AWS CodeBuild cuida do CI/CD."

**Transição:** "Vou detalhar as duas trilhas de código: CI/CD e treinamento contínuo."

---

## Slide 8 — Pipelines CI/CD + CT  `alvo: 4:45–5:30`
Reforce a separação entre as duas trilhas — essa é a "contribuição central" do slide, vale dizer explicitamente.

> "A trilha de CI/CD é direta: commit, build da imagem, push para o ECR, deploy no EKS via AWS CodeBuild. A trilha de treinamento contínuo é inteiramente serverless: Glue, EventBridge e três funções Lambda que treinam, avaliam por F1-score e promovem o modelo automaticamente, sem intervenção manual. O ponto central é que essas duas trilhas são desacopladas — código e ciclo de vida do modelo evoluem de forma independente, o que era justamente uma lacuna identificada na literatura."

**Transição:** "A outra parte da Fase 3 é como esses serviços escalam."

---

## Slide 9 — Autoscaling: HPA (Inferência) + KEDA (Process)  `alvo: 5:30–6:20`
**Atenção: ponto historicamente corrigido — não confunda os dois mecanismos.** Fale devagar aqui, é o ponto mais provável de gerar pergunta da banca.

> "Dois serviços, dois mecanismos de escalonamento, e isso é intencional. O serviço de Inferência — a API síncrona que responde o score — escala por um HPA tradicional baseado em CPU, de 8 a 10 réplicas, porque a carga dele é correlacionada ao uso de CPU. Já o serviço Process — o worker assíncrono que consome a fila de resultados — escala via KEDA, baseado na profundidade da fila SQS FIFO, de 2 a 5 réplicas, porque a carga dele chega em rajadas, desacopladas de CPU. Não é 'KEDA para tudo' — é o mecanismo certo para o padrão de carga de cada serviço."

**Transição:** "Com a arquitetura e os pipelines definidos, a Fase 4 foi validar tudo isso experimentalmente."

---

## Slide 10 — Resultados Preliminares  `alvo: 6:20–7:25`
Este slide fundiu setup + achado principal. O clímax da apresentação — fale com mais ênfase, mas sem se alongar no método (uma frase basta). Diga **"preliminar"** aqui, é obrigatório.

> "Usei Locust com 100 payloads reais de transações 3DS, no endpoint de autorização, em DEV e Staging. Durante os testes sequenciais em DEV, sem HTTP keepalive, observei picos isolados e recorrentes — uma requisição levou 5,2 segundos, outra 2,6 segundos, no meio de requisições normais de 180ms. O diagnóstico: sem keepalive, o NLB encerra a conexão TCP por timeout, e cada nova requisição reconecta toda a cadeia de rede, o que adiciona de 1 a 4 segundos. Habilitando o keepalive, sem mudar infraestrutura, modelo ou algoritmo, o p95 caiu de 1.100 milissegundos para 330 — uma redução de 70%. Repito: isso é um resultado **preliminar**, do ambiente DEV; o SLA contratado de 10.000 requisições por segundo ainda não foi validado — fica para o TCC II."

**Transição:** "Diante disso, esse é o estado atual e o que vem a seguir."

---

## Slide 11 — Estado Atual & Trabalhos Futuros  `alvo: 7:25–8:15`
Este slide fundiu status + próximos passos. Rápido na tabela de status (uma frase), um pouco mais de tempo nos 3 próximos passos.

> "Dos quatro objetivos específicos, três estão totalmente implementados; a governança e o escalonamento por eventos estão validados parcialmente — falta o teste sob carga de spike. Para o TCC II, os pontos principais são: validar experimentalmente as metas de 100 RPS e de 10.000 requisições por segundo do SLA contratado; evoluir a promoção de modelos para um canary release, em vez da promoção imediata atual; e avançar para detecção automática de concept drift, usando um componente que já coleta as métricas necessárias. Essas limitações não invalidam o que já foi construído — elas delimitam precisamente o que falta para a entrega final."

**Transição:** "Fechando, a conclusão parcial deste momento do trabalho."

---

## Slide 12 — Conclusão Parcial  `alvo: 8:15–8:55`
Feche com força — repita o achado central mais uma vez, é o que fica na memória da banca.

> "Os resultados até aqui indicam que integrar MLOps a pipelines DevOps de forma eficiente exige, no mínimo: separação arquitetural entre CI/CD e treinamento contínuo, automação serverless para o ciclo de vida do modelo, infraestrutura modularizada por domínio, e testes de carga com payloads reais como parte do processo — não uma etapa opcional. O achado preliminar mais relevante segue sendo a otimização de HTTP keepalive, com redução de 70% no p95, sem qualquer mudança de infraestrutura, modelo ou algoritmo. Para o TCC II, o foco é consolidar essa validação rumo ao SLA real de 10.000 requisições por segundo, e finalizar a redação do artigo."

**Transição:** "Muito obrigado."

---

## Slide 13 — Obrigado  `alvo: 8:55–9:10`
> "Muito obrigado pela atenção. Fico à disposição para perguntas."

*(Isso encerra a fala em ~9:10, deixando ~50 segundos de folga antes do limite de 10 minutos — use essa folga para respirar entre slides, não para se alongar em nenhum ponto específico.)*

---

## Anexos A–D (slides 14–17) — material de apoio, fora dos 10 minutos

Após o slide 13, o arquivo contém 4 slides extras com os diagramas de arquitetura originais do projeto (fonte: documentação interna do cliente). **Não fazem parte da fala cronometrada** — não avance até eles no fluxo normal. Use-os apenas se a banca pedir detalhe visual de infraestrutura:

- **Anexo A** — Infraestrutura, visão geral (backend → API Gateway → VPC Link → NLB → EKS → trilha CT completa)
- **Anexo B** — Fluxo 1: Inferência síncrona, passo a passo (Normalize → Extract → Enrich → Model Invoke → Build Response)
- **Anexo C** — Fluxo 2: Process assíncrono (SQS FIFO → EKS → DynamoDB/Firehose → S3)
- **Anexo D** — Fluxo 3: MLOps em 4 raias (ETL → Feature Engineering → Treinamento → Registro)

Esses 4 diagramas confirmam visualmente, com uma fonte independente, dois pontos que já estão no artigo e na fala: **não há ALB no caminho de inferência** (Anexos A e B mostram API Gateway → NLB direto) e o agendamento do Glue Job em "domingo 05:00 BRT" (Anexo D) equivale a "08h00 UTC" (mesmo horário, fusos diferentes) — não é uma contradição com o que está escrito no artigo.

---

## Perguntas prováveis do orientador/banca — e como responder

**"Por que só ~100 RPS testados se o SLA é de 10.000 req/s?"**
> "Essa é exatamente a delimitação de escopo da TCC I: os 100 RPS são uma meta interna de validação, viável no tempo e infraestrutura desta etapa. O SLA de 10.000 req/s é o alvo contratual de produção, e a validação dessa escala fica para a TCC II — envolve testes de carga maiores e possivelmente ajustes de infraestrutura."

**"Qual foi exatamente sua contribuição, já que o modelo foi feito por outra pessoa?"**
> "Minha autoria é a camada de DevOps/Infraestrutura: todo o Terraform, a arquitetura Kubernetes, os pipelines de CI/CD e CT, e o monitoramento. O modelo de Machine Learning — as features e o algoritmo — foi construído por outra frente da equipe, de Data Science. Isso está documentado na definição de papéis do projeto, e é justamente essa separação de responsabilidades que o TCC discute como boa prática de MLOps."

**"Existe um Application Load Balancer na arquitetura?"**
> "Não, na configuração atual. A cadeia é API Gateway, VPC Link, NLB, direto para os pods via TargetGroupBinding. Não há ALB no caminho de inferência."

**"Por que a Inferência usa HPA por CPU e o Process usa KEDA por fila, e não os dois pelo mesmo mecanismo?"**
> "Porque o padrão de carga é diferente. A Inferência responde de forma síncrona e tem uso de CPU proporcional ao tráfego. O Process consome uma fila de forma assíncrona e em rajadas — a profundidade da fila é um sinal mais direto de demanda real do que a CPU nesse caso."

**"Os dados e documentos internos do cliente podem ser citados no artigo final?"**
> "Estão classificados como restritos. Qualquer citação literal depende de autorização formal da empresa — algo que pretendo buscar antes da versão final do artigo, ou, alternativamente, manter a descrição em termos gerais e anonimizados, como já é feito na apresentação."

**"O que exatamente mudou entre TCC I e TCC II?"**
> "Na TCC I entrego a arquitetura completa implementada e um achado preliminar de latência. Na TCC II, consolido a validação experimental completa — incluindo as metas reais de throughput, o comportamento sob picos de carga, e a análise estatística nos dois ambientes — além de finalizar a redação e a conclusão do artigo."

**"Por que a apresentação ficou mais curta / o que foi cortado em relação a uma versão anterior?"**
> "O cronograma da pré-banca foi ajustado para 10 minutos. Condensei conteúdos correlatos — por exemplo, contexto do cliente entrou junto do problema de pesquisa, e setup do teste entrou junto do resultado — sem remover nenhuma informação factual, só a redundância entre slides."

---

## Resumo de tempo (checkpoints)

Com 10 minutos, a margem de manobra é pequena — trate estes checkpoints como sinais de alerta, não como pontos opcionais.

| Checkpoint | Tempo alvo | Se estiver atrasado... |
|---|---|---|
| Fim do slide 4 (Objetivos) | ~2:35 | Encurte o slide 3 — corte a citação de Sculley e vá direto ao contexto do cliente |
| Fim do slide 7 (Arquitetura) | ~4:45 | Resuma o slide 6 (lacunas) em uma frase única, sem citar as 5 uma a uma |
| Fim do slide 10 (Resultados) | ~7:25 | Encurte o slide 11 — cite só 1 próximo passo (throughput), não os 3 |
| Fim do slide 12 (Conclusão) | ~8:55 | Nunca corte a conclusão nem o achado do keepalive — é o fechamento que fica na memória da banca |

**Se, mesmo assim, o ensaio mostrar que 10 minutos não são suficientes:** os candidatos a corte adicional são (em ordem de prioridade) o segundo parágrafo do slide 3 (delimitação de escopo pode ser resumida em uma frase) e o slide 6 (Fase 1 pode virar uma única frase: "o levantamento bibliográfico identificou 5 lacunas, todas resolvidas na arquitetura a seguir"). Não corte o slide 9 (HPA vs. KEDA) nem o slide 10 (achado do keepalive) — são o núcleo técnico e empírico do trabalho.

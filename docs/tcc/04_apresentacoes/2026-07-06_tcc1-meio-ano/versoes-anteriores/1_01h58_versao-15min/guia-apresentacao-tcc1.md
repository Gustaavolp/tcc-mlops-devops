# Guia de Apresentação — TCC I (Apresentação de Andamento)

**Duração alvo: 15 minutos  ·  17 slides  ·  Arquivo: `Apresentacao_TCC1_MeioAno_Gustavo.pptx`**

## Como usar este guia

Isto não é um script para decorar palavra por palavra — é um roteiro de pontos-chave. Fale com suas próprias palavras; o guia existe para você não esquecer o essencial e não perder tempo em detalhes secundários. Os tempos são cumulativos: se ao chegar num "checkpoint" você estiver muito acima do tempo, corte os pontos marcados como **(se sobrar tempo)** nos slides seguintes.

**Regra de ouro nº 1 (feedback do orientador):** não leia o slide. Ele já mostra a informação — sua fala deve *complementar*, não repetir.

**Regra de ouro nº 2 (feedback do orientador):** em qualquer momento que mencionar números de latência/throughput dos testes, diga a palavra **"preliminar"** em voz alta. Isso já está escrito nos slides 12 e 13, mas reforce oralmente — é o ponto mais importante do feedback recebido.

---

## Checklist antes de começar
- [ ] Cronômetro visível (celular ou relógio) — ensaiar pelo menos 1x com cronômetro real.
- [ ] Saber de cor os 3 números centrais: **93% recall**, **P95 1.100ms → 330ms (−70%)**, **10.000 req/s (SLA) vs. ~47 RPS (testado)**.
- [ ] Ter lido a seção "Perguntas prováveis" no fim deste guia pelo menos uma vez.

---

## Slide 1 — Capa  `alvo: 0:00–0:20`
Só se apresente e apresente o tema. Não precisa ler o subtítulo do slide.

> "Boa tarde. Meu nome é Gustavo Liebl Pereira, e esta é a apresentação de andamento do meu TCC I, orientado pelo professor Marcelo Semmer, sobre integração de MLOps em pipelines DevOps."

**Transição:** "Antes de entrar no conteúdo técnico, um resumo rápido da agenda."

---

## Slide 2 — Agenda  `alvo: 0:20–0:50`
Não leia os 14 itens um por um. Agrupe em blocos.

> "A apresentação tem quatro blocos: primeiro o problema e o contexto real que originou este trabalho; depois a metodologia em quatro fases — bibliografia, infraestrutura, pipelines e validação experimental; e por fim o estado atual e o que fica para o TCC II. Como é TCC I, os resultados que vou mostrar são um preview — a validação completa fica para a próxima etapa."

**Transição:** "Vamos começar pelo problema de pesquisa."

---

## Slide 3 — Problema de Pesquisa  `alvo: 0:50–1:55`
Foco: a lacuna Data Science vs. Engenharia é conhecida na literatura — não precisa explicar cada bullet dos dois quadros, só apontar o contraste.

> "Do lado de Data Science, o modelo funciona bem no notebook. Do lado de Engenharia, falta tudo que é necessário para produção: versionamento, deploy automatizado, monitoramento. A literatura confirma isso — Gartner estima que 85% dos projetos de ML nunca chegam à produção, e Sculley et al. já apontavam em 2015 que a maior parte do código de um sistema de ML real é infraestrutura, não o modelo em si."

Depois conecte com a realidade do projeto **sem citar o nome do cliente** (a apresentação já está anonimizada):

> "Este trabalho nasce de um caso real: uma plataforma de detecção de fraude para uma empresa de grande porte do setor de pagamentos eletrônicos, rodando em produção na AWS."

**Transição:** "E esse contexto real é justamente o próximo ponto."

---

## Slide 4 — Contexto Real / Necessidade do Cliente  `alvo: 1:55–3:15`
Este é o slide que dá **força de fonte primária** ao trabalho — vale o tempo. Destaque 3 coisas: (1) a demanda é real e documentada, (2) o SLA contratado é rigoroso, (3) seu escopo de autoria é delimitado.

> "O ponto de partida não foi uma hipótese acadêmica — foi uma demanda formal do cliente. Havia um MVP já validado com 93% de recall de fraude, e o cliente pediu formalmente, em kick-off, a evolução desse MVP para um motor preditivo operacional, com prazo definido e um SLA contratual rigoroso: latência p95 abaixo de 500ms, 99,9% de disponibilidade, conformidade com a LGPD e **throughput de 10.000 requisições por segundo**."

Diga isso com clareza — é importante para não gerar confusão depois:

> "É fundamental deixar claro o escopo da minha autoria aqui: minha atuação foi como Engenheiro DevOps — Terraform, Kubernetes, CI/CD e monitoramento. O treinamento do modelo de Machine Learning em si — features e algoritmo — foi de outra frente da equipe, de Data Science. Isso está documentado na documentação interna do projeto."

Se achar necessário, mencione rapidamente a confidencialidade: "os documentos-fonte são internos e restritos; qualquer citação literal no artigo final depende de autorização da empresa."

**Transição:** "Com esse contexto, a pergunta de pesquisa e os objetivos ficam mais concretos."

---

## Slide 5 — Pergunta de Pesquisa e Objetivos  `alvo: 3:15–4:15`
Leia a pergunta de pesquisa (ela é densa, vale ler literalmente uma vez). Os 5 objetivos específicos, **não leia** — só cite rapidamente o padrão comum entre eles.

> "A pergunta de pesquisa que guia este trabalho é: como integrar de forma eficiente, escalável e automatizada o ciclo de vida de MLOps em pipelines DevOps, garantindo entrega contínua e governança em produção? A partir disso, defini cinco objetivos específicos, que cobrem desde a arquitetura de integração até a validação experimental do escalonamento — todos voltados a um único objetivo geral: demonstrar, num projeto prático em nuvem, as boas práticas e os desafios reais dessa integração."

**Transição:** "Para alcançar esses objetivos, segui uma metodologia em quatro fases."

---

## Slide 6 — Metodologia — Visão Geral  `alvo: 4:15–5:00`
Aponte o fluxo, não leia os cards.

> "A metodologia é uma pesquisa aplicada, de caráter experimental e construtivo: eu mesmo projetei, implementei e validei a plataforma em produção — o sistema construído é, ao mesmo tempo, o artefato de pesquisa e o instrumento de validação. Ela se divide em quatro fases sequenciais: levantamento bibliográfico, infraestrutura como código, pipelines de CI/CD e treinamento contínuo, e validação experimental. Vou detalhar rapidamente cada uma."

**Transição:** "Começando pela Fase 1."

---

## Slide 7 — Fase 1: Levantamento Bibliográfico  `alvo: 5:00–5:55`
Não leia as 5 lacunas com as citações — resuma a ideia central de cada uma em poucas palavras, olhando o slide como apoio visual.

> "Fiz um levantamento em IEEE Xplore, ACM Digital Library e Google Scholar, priorizando trabalhos com implementação prática, não só taxonomias teóricas. Identifiquei cinco lacunas que guiaram as decisões de arquitetura: falta de separação clara entre CI/CD e treinamento contínuo, pouca comparação entre MLflow gerenciado e self-hosted, autoscaling orientado a eventos pouco explorado para cargas de ML, o impacto de otimizações de rede como HTTP keepalive praticamente não documentado, e modularização de IaC por domínio funcional pouco formalizada. Essas cinco lacunas aparecem resolvidas, uma a uma, na arquitetura que vou mostrar a seguir."

**Transição:** "A segunda fase foi a infraestrutura como código."

---

## Slide 8 — Fase 2: Infraestrutura como Código  `alvo: 5:55–6:50`
A tabela fala por si — não leia linha por linha. Destaque o "diferencial".

> "Toda a infraestrutura foi codificada em Terraform, organizada em 15 módulos e 5 stacks independentes — foundation, mlops, platform, platform-k8s e platform-lambdas. O diferencial aqui é modularizar por domínio funcional, e não por ambiente: cada stack pode ser aplicada, destruída e recriada de forma isolada, e o state é remoto em S3 com locking nativo. Isso foi replicado em dois ambientes com paridade de configuração: DEV na Virgínia e Staging em São Paulo."

**Transição:** "Essa infraestrutura sustenta a arquitetura que vou mostrar agora, de forma simplificada."

---

## Slide 9 — Arquitetura da Plataforma  `alvo: 6:50–8:00`
Este é o slide mais denso — vá camada por camada, apontando, sem ler as setas literalmente.

> "A arquitetura tem quatro trilhas. A de inferência em tempo real: a transação 3DS chega via API Gateway, passa por um NLB e vai direto para os pods do serviço de inferência em FastAPI, que consulta o DynamoDB como feature store e retorna o score. A de processamento assíncrono: o resultado da inferência vai para uma fila SQS FIFO, consumida por um worker que escala via KEDA, e os dados seguem via Kinesis Firehose para o data lake em S3. A de treinamento contínuo: toda semana, aos domingos, um job Glue processa os logs, dispara funções Lambda que treinam um novo modelo no SageMaker e o registram no MLflow — só promovendo para produção se o novo modelo superar o atual. E por trás de tudo isso, Terraform provisiona a infraestrutura e o AWS CodeBuild cuida do CI/CD."

**Transição:** "Vou detalhar as duas primeiras trilhas — CI/CD e treinamento contínuo — no próximo slide."

---

## Slide 10 — Pipelines CI/CD + CT  `alvo: 8:00–8:55`
Reforce a separação entre as duas trilhas — essa é a "contribuição central" do slide.

> "Um ponto que corrigi ao longo do trabalho: a ferramenta de CI/CD real é o AWS CodeBuild, não GitHub Actions como constava numa versão anterior do artigo. A trilha de CI/CD é simples: commit, build da imagem, push para o ECR, deploy no EKS. A trilha de treinamento contínuo é inteiramente serverless: Glue, EventBridge e três funções Lambda que treinam, avaliam e promovem o modelo automaticamente, sem intervenção manual, comparando o F1-score do candidato contra o modelo em produção. O ponto central aqui é que essas duas trilhas são desacopladas — código e ciclo de vida do modelo evoluem de forma independente."

**Transição:** "A outra parte da Fase 3 é o escalonamento dos serviços."

---

## Slide 11 — Autoscaling: HPA (Inferência) + KEDA (Process)  `alvo: 8:55–10:00`
**Atenção: este slide foi corrigido recentemente — não confunda os dois mecanismos.** Fale devagar aqui, é um ponto que pode gerar pergunta.

> "Um ponto importante para deixar claro: existem dois serviços com dois mecanismos de escalonamento diferentes, e isso é intencional. O serviço de Inferência — a API síncrona que responde o score — escala por um HPA tradicional baseado em CPU, de 8 a 10 réplicas, porque a carga dele é razoavelmente correlacionada ao uso de CPU. Já o serviço Process — o worker assíncrono que consome a fila de resultados — escala via KEDA, baseado na profundidade da fila SQS, de 2 a 5 réplicas, porque a carga dele chega em rajadas, desacopladas de CPU. Ou seja: não é 'KEDA para tudo' — é o mecanismo certo para o padrão de carga de cada serviço."

**Transição:** "Com a arquitetura e os pipelines definidos, a Fase 4 foi validar tudo isso experimentalmente."

---

## Slide 12 — Validação Experimental: Setup  `alvo: 10:00–11:10`
Diga "preliminar" aqui.

> "Para a validação, usei Locust com 100 payloads reais de transações 3DS — não payloads sintéticos. O SLA que defini para esta etapa de validação é mais conservador que o contratual: p95 abaixo de 500ms, disponibilidade de 100%, throughput mínimo de 100 RPS. Até agora, executei cinco cenários preliminares em dois ambientes, comparando o comportamento antes e depois de uma otimização que vou detalhar no próximo slide. É importante frisar: o SLA de produção contratado pelo cliente é 10.000 requisições por segundo — os cenários que rodei até aqui validam uma fração desse volume; a validação completa de throughput fica para o TCC II."

**Transição:** "E o achado mais relevante desses testes preliminares é este."

---

## Slide 13 — Preview de Resultados  `alvo: 11:10–12:25`
O clímax da apresentação. Fale com mais ênfase aqui — é o achado que "vende" o trabalho.

> "Durante os testes sequenciais em DEV, sem HTTP keepalive, observei picos isolados e recorrentes: a requisição 37 levou 5,2 segundos, a 45 levou 2,6 segundos, no meio de requisições normais de 180ms. O diagnóstico: sem keepalive, o NLB encerra a conexão TCP por timeout, e cada nova requisição precisa reconectar toda a cadeia de rede — API Gateway, NLB, até o pod — o que adiciona de 1 a 4 segundos. Habilitando o keepalive, sem mudar nada de infraestrutura, modelo ou algoritmo, o p95 caiu de 1.100 milissegundos para 330 milissegundos — uma redução de 70%. Repito: isso é um resultado preliminar, do ambiente DEV; a validação completa nos dois ambientes e nas metas de throughput fica para o TCC II."

**Transição:** "Diante disso, esse é o estado atual do trabalho."

---

## Slide 14 — Estado Atual do Trabalho  `alvo: 12:25–13:10`
Rápido — é um "status report", não precisa de fala longa.

> "Dos cinco objetivos específicos, quatro estão implementados; o escalonamento orientado a eventos está validado parcialmente — falta o teste sob carga de spike. Na redação do artigo, introdução, referencial teórico e metodologia já estão prontos, com mais de 15 referências; a seção de resultados ainda está em expansão, e a conclusão final e revisão ABNT ficam para a reta final."

**Transição:** "O que resta, então, é claramente delimitado — são os trabalhos futuros."

---

## Slide 15 — Trabalhos Futuros  `alvo: 13:10–13:55`
Não leia as 5 linhas da tabela — cite 2 ou 3 mais importantes.

> "Para o TCC II, os pontos principais são: validar experimentalmente as metas de 100 RPS e de 10.000 requisições por segundo do SLA contratado, incluindo o comportamento do KEDA sob picos; avançar para detecção automática de concept drift, usando um componente que já coleta as métricas necessárias; e evoluir a promoção de modelos para um canary release, em vez da promoção imediata atual. Essas limitações não invalidam o que já foi construído — elas delimitam precisamente o que falta para a entrega final."

**Transição:** "Fechando, a conclusão parcial deste momento do trabalho."

---

## Slide 16 — Conclusão Parcial  `alvo: 13:55–14:40`
Feche com força — repita o achado central mais uma vez.

> "Os resultados até aqui indicam que integrar MLOps a pipelines DevOps de forma eficiente exige, no mínimo: separação arquitetural clara entre CI/CD e treinamento contínuo, automação serverless para o ciclo de vida do modelo, infraestrutura modularizada por domínio, governança centralizada via Model Registry, e testes de carga com payloads reais como parte do processo — não uma etapa opcional. O achado preliminar mais relevante segue sendo a otimização de HTTP keepalive, com redução de 70% no p95, sem qualquer mudança de infraestrutura, modelo ou algoritmo. Para o TCC II, o foco é consolidar essa validação experimental rumo ao SLA real de 10.000 requisições por segundo, e finalizar a redação do artigo."

**Transição:** "Muito obrigado."

---

## Slide 17 — Obrigado  `alvo: 14:40–15:00`
> "Muito obrigado pela atenção. Fico à disposição para perguntas."

---

## Perguntas prováveis do orientador/banca — e como responder

**"Por que só ~47 RPS testados se o SLA é de 10.000 req/s?"**
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

---

## Resumo de tempo (checkpoints)

| Checkpoint | Tempo alvo | Se estiver atrasado... |
|---|---|---|
| Fim do slide 5 (Objetivos) | ~4:15 | Corte detalhes do slide 3 (não leia os dois quadros por completo) |
| Fim do slide 9 (Arquitetura) | ~8:00 | Resuma o slide 7 (lacunas) em uma frase só |
| Fim do slide 13 (Preview Resultados) | ~12:25 | Encurte o slide 14 — é só um status, pode ser rápido |
| Fim do slide 16 (Conclusão) | ~14:40 | Não pule a conclusão — se precisar cortar, corte o slide 15 (trabalhos futuros) pela metade |

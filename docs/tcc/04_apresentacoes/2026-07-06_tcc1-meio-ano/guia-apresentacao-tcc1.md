# Guia de Apresentação — TCC I (Pré-Banca / Proposta de Pesquisa)

**Duração alvo: 10 minutos  ·  16 slides  ·  Arquivo: `Apresentacao_TCC1_MeioAno_Gustavo.pptx`**

> ⚠️ Reestruturação motivada por orientação direta do professor Marcelo Semmer: *"vocês ainda estão apresentando a proposta da pesquisa, não os resultados finais. Foquem bem no tema, problema, objetivos, justificativa, referencial principal e metodologia"*, desenvolvendo a apresentação **até a parte de Materiais e Métodos**.
>
> A versão anterior de 17 slides "de andamento" (arquitetura implementada, autoscaling com números reais, resultados preliminares e conclusão) **não seguia esse escopo** — apresentava o projeto como já implementado e validado, apropriado para uma defesa final, não para uma pré-banca de proposta. Está preservada em `backup_andamento_completo_2026-07-06/`.
>
> **Os 4 diagramas técnicos do estudo de caso foram reincorporados**, a pedido, dentro do bloco de Materiais e Métodos (slides 10–13) — mas com um enquadramento diferente do da versão anterior: agora são apresentados como **arquitetura proposta / material de referência da proposta**, não como evidência de algo já implementado e validado. Nenhum diagrama traz números de resultado.
>
> **Simplificação de conteúdo (última rodada):** o slide 5 (Justificativa) passou de 3 colunas separadas para um único argumento em destaque; os antigos slides 7 e 8 (Referencial Teórico 1/2 e 2/2) foram **fundidos em um único slide** com os 4 pilares em grade 2x2 e frases curtas em vez de parágrafos; e o slide de Materiais e Métodos perdeu o bloco introdutório redundante e a nota de autoria repetida (já dita no slide 3). Isso reduziu a apresentação de 17 para **16 slides** e devolveu ~40s de folga ao orçamento de 10 minutos.
>
> **Continua sem estar nesta versão**: números de resultados de teste (latência, recall, throughput testado), tabela de "estado atual" e conclusão parcial — isso segue reservado para a defesa completa da TCC I.

## Como usar este guia

Isto não é um script para decorar palavra por palavra — é um roteiro de pontos-chave. Fale com suas próprias palavras. A contagem de palavras dos textos abaixo, a um ritmo de fala formal (110–140 palavras/minuto), soma bem menos que o orçamento de 10 minutos — os tempos "alvo" cumulativos abaixo já embutem boa folga para pausas, ênfase e transições. Ainda assim, ensaie com cronômetro real.

**Regra de ouro nº 1 (feedback do orientador, já reforçada antes):** não leia o slide. Ele já mostra a informação — sua fala deve *complementar*, não repetir. Isso vale em dobro para os 4 slides de diagrama (10–13) e para o slide 7 (Referencial Teórico, agora em cards curtos): é reforço visual, uma frase basta, não descreva cada ícone nem releia cada card.

**Regra de ouro nº 2 (escopo desta pré-banca):** se a banca perguntar sobre resultados ou números de teste, é esperado responder que **isso ainda não foi apresentado nesta etapa** — a pré-banca cobre a proposta até Materiais e Métodos, incluindo a arquitetura *proposta*; resultados e conclusão virão na defesa completa da TCC I. Ao falar dos diagramas, use sempre linguagem de proposta ("será implementado e validado", "arquitetura de referência para o estudo") — nunca linguagem de resultado já obtido.

---

## Checklist antes de começar

- [ ] Cronômetro visível — ensaiar pelo menos 2x com cronômetro real.
- [ ] Ter internalizado a pergunta de pesquisa de cor (slide 4).
- [ ] No slide 7 (Referencial Teórico): treinar 1 frase curta por pilar (4 no total), sem reler os cards.
- [ ] Nos 4 slides de diagrama (10–13): treinar a frase única de cada um, sempre em tom de proposta ("será implementado/validado"), nunca de resultado.
- [ ] Ter lido a seção "Perguntas prováveis" no fim deste guia pelo menos uma vez.
- [ ] Lembrar: nada de números de resultado nem conclusão — se vier à mente citar uma métrica de teste, é sinal de que se está fora do escopo pedido.
- [ ] Ter internalizado que, se a banca fizer uma pergunta durante a fala, isso consome tempo do orçamento de 10 minutos — responda de forma direta e curta.

---

## Slide 1 — Capa  `alvo: 0:00–0:15`

> "Boa tarde. Meu nome é Gustavo Liebl Pereira. Esta é a pré-banca do meu TCC I, orientado pelo professor Marcelo Semmer, sobre integração de MLOps em pipelines DevOps."

**Transição:** "Vou direto à agenda."

---

## Slide 2 — Agenda  `alvo: 0:15–0:40`

> "A apresentação segue a proposta de pesquisa até Materiais e Métodos: tema, problema, justificativa, objetivos, referencial teórico, metodologia e a arquitetura proposta para o estudo de caso. Não entro em resultados finais — essa validação completa fica para a etapa seguinte do trabalho."

**Transição:** "Começando pelo tema e o contexto."

---

## Slide 3 — Tema e Contexto  `alvo: 0:40–1:25`

> "O tema nasce de um gargalo real da Engenharia de Software: a transição de modelos experimentais de Machine Learning para sistemas produtivos resilientes. A literatura é clara — a maior parte do código de um sistema de ML real é infraestrutura, não o modelo, e a maioria dos projetos nunca chega à produção. A motivação prática vem de um estudo de caso real: uma plataforma de detecção de fraude em transações eletrônicas, com exigências rígidas de SLA e conformidade regulatória — um cenário típico de produção crítica de ML. Minha autoria nesse projeto é a camada de Engenharia DevOps; o modelo de Machine Learning é de outra frente da equipe."

**Transição:** "Esse contexto expõe diretamente o problema de pesquisa."

---

## Slide 4 — Problema de Pesquisa  `alvo: 1:25–2:10`

Vale ler a pergunta de pesquisa literalmente, é o ponto mais citável do slide.

> "Do lado de Data Science, falta API de servimento e pipeline de retreinamento; do lado de Engenharia, falta deploy automatizado e governança — essa desconexão gera a pergunta de pesquisa: como integrar de forma eficiente, escalável e automatizada o ciclo de vida de MLOps em pipelines de DevOps, garantindo entrega contínua e governança operacional em produção?"

**Transição:** "Isso justifica diretamente por que este trabalho importa."

---

## Slide 5 — Justificativa  `alvo: 2:10–2:55`

Slide de argumento único (era 3 colunas separadas — técnica/prática/acadêmica — agora é uma cadeia só). Deixe a frase em destaque falar por si; sua fala complementa, não repete.

> "A justificativa parte de um único fato: a maior parte do esforço real em um sistema de ML em produção está na engenharia ao redor do modelo, não no algoritmo — é o que Sculley et al. chamam de dívida técnica oculta. Mesmo assim, a maioria das organizações trata MLOps como extensão informal do DevOps, sem arquitetura, automação ou governança adequadas. Este trabalho propõe justamente essa arquitetura de referência, unindo uma urgência real de mercado a uma lacuna já documentada na literatura."

**Transição:** "A partir dessa justificativa, defino os objetivos do trabalho."

---

## Slide 6 — Objetivos  `alvo: 2:55–3:40`

Não leia os 5 objetivos específicos um a um — aponte o padrão comum entre eles.

> "O objetivo geral é demonstrar, num projeto prático em nuvem, a implementação de uma arquitetura de MLOps integrada a pipelines DevOps. Os cinco objetivos específicos cobrem desde o projeto da integração DevOps e MLOps até a infraestrutura como código, os pipelines de CI/CD e treinamento contínuo, a governança via MLflow e a validação do escalonamento orientado a eventos."

**Transição:** "Esses objetivos se apoiam em um referencial teórico específico."

---

## Slide 7 — Referencial Teórico  `alvo: 3:40–4:25`

Slide fundido (antes eram 2 slides separados) — 4 cards em grade 2x2, cada um com uma frase curta. Não releia os cards, só nomeie o pilar e complemente com uma frase de contexto.

> "O referencial teórico se apoia em quatro pilares. Sculley et al. mostram que a dívida técnica em sistemas de ML é majoritariamente estrutural — configuração, dados e monitoramento, não o algoritmo. Kreuzberger et al. definem o MLOps como a padronização do ciclo de vida, exigindo versionamento de código, modelo e dado, com o Continuous Training retreinando automaticamente quando a performance degrada. Karimibiuki et al. tratam a infraestrutura como código, garantindo paridade entre ambientes. E a literatura de Kubernetes e KEDA mostra que o escalonamento orientado a eventos escala pela demanda real da fila, não por uma métrica indireta como CPU."

**Transição:** "Com essa base teórica, a metodologia da pesquisa."

---

## Slide 8 — Metodologia — Visão Geral  `alvo: 4:25–5:10`

Aponte o fluxo visual das 4 fases, não leia os cards em detalhe.

> "A pesquisa é aplicada, experimental e construtiva — o próprio sistema implementado é, ao mesmo tempo, o artefato e o instrumento de validação. Ela se organiza em quatro fases: levantamento bibliográfico, desenvolvimento da infraestrutura via Terraform, implementação dos pipelines de CI/CD e MLflow, e por fim a validação experimental planejada, com testes de carga comparando mecanismos de escalonamento."

**Transição:** "Detalhando os materiais, o método de validação planejado e a arquitetura proposta."

---

## Slide 9 — Materiais e Métodos  `alvo: 5:10–5:50`

Ritmo firme, sem se aprofundar em cada item da lista de materiais — os rótulos já são curtos.

> "Como materiais, a pesquisa utiliza Terraform para infraestrutura, Docker e Kubernetes via Amazon EKS para orquestração, pipelines de CI/CD declarativos, MLflow para governança de modelos, e filas de mensagens com KEDA para escalonamento orientado a eventos — tudo em Python e HCL. O método de validação planejado é um teste de carga com Locust, simulando tráfego real e comparando o comportamento do escalonamento tradicional por CPU com o escalonamento orientado a eventos sob picos de demanda. A execução e a análise detalhada desses testes ficam para a etapa seguinte do trabalho."

**Transição:** "A arquitetura de referência que documenta essa proposta é esta:"

---

## Slide 10 — Arquitetura Proposta: Visão Geral da Infraestrutura  `alvo: 5:50–6:15`

Diagrama de referência do estudo de caso (imagem não alterada) — é reforço visual da proposta, uma frase basta. Enfatize que ainda será implementado/validado, não que já foi.

> "Este diagrama documenta a visão geral da infraestrutura proposta para o estudo de caso — a camada de rede, o cluster Kubernetes e as trilhas de dados que serão implementadas e validadas na etapa seguinte deste trabalho."

**Transição:** "Detalhando o fluxo síncrono de inferência:"

---

## Slide 11 — Arquitetura Proposta: Fluxo de Inferência (Síncrono)  `alvo: 6:15–6:40`

> "Aqui está o fluxo de inferência síncrona proposto: a requisição chega, passa pela camada de rede, é processada pelo serviço de inferência e retorna o score — o caminho que será instrumentado nos testes de validação da próxima etapa."

**Transição:** "E o fluxo assíncrono de processamento, essencial para o objetivo de escalonamento:"

---

## Slide 12 — Arquitetura Proposta: Fluxo de Processamento (Assíncrono)  `alvo: 6:40–7:05`

> "Este é o fluxo de processamento assíncrono proposto, baseado em fila de mensagens — o cenário-chave para testar o escalonamento orientado a eventos, que é um dos objetivos deste trabalho."

**Transição:** "Por fim, o fluxo de treinamento contínuo:"

---

## Slide 13 — Arquitetura Proposta: Fluxo de Treinamento Contínuo (MLOps)  `alvo: 7:05–7:30`

> "Por fim, o fluxo de treinamento contínuo proposto, do processamento de dados ao registro condicional de modelos — a automação que será avaliada quanto à governança na etapa de validação."

**Transição:** "Com a proposta situada, o cronograma até a conclusão do trabalho."

---

## Slide 14 — Cronograma  `alvo: 7:30–8:10`

> "A partir desta proposta, os próximos passos são: consolidar a implementação da infraestrutura e dos pipelines descritos; executar a validação experimental planejada; analisar os resultados obtidos e redigir as seções de resultados e discussão; e, por fim, consolidar a conclusão e finalizar a redação do artigo completo."

**Transição:** "Fechando, as referências que sustentam esta proposta."

---

## Slide 15 — Referências Principais  `alvo: 8:10–8:35`

Não leia a lista completa — cite as 2-3 mais centrais e aponte que o restante está no slide.

> "As referências principais que sustentam esta proposta incluem Sculley, sobre dívida técnica; Treveil, sobre a prática de MLOps; Kreuzberger, sobre a arquitetura padrão; Karimibiuki, sobre infraestrutura como código; e o AWS Well-Architected Framework, com boas práticas de Machine Learning na nuvem."

**Transição:** "Muito obrigado."

---

## Slide 16 — Obrigado  `alvo: 8:35–8:55`

> "Muito obrigado pela atenção. Fico à disposição para perguntas."

*(Isso encerra a fala por volta de 8:55, deixando mais de 1 minuto de folga antes do limite de 10 minutos — bem mais espaço do que na versão anterior, graças à fusão do Referencial Teórico e ao corte no slide de Materiais e Métodos. Ainda assim, ensaie com cronômetro real.)*

---

## Perguntas prováveis do orientador/banca — e como responder

**"Se isso é uma proposta, por que a apresentação mostra diagramas de arquitetura?"**
> "Os diagramas fazem parte de Materiais e Métodos — documentam a arquitetura de referência que serve de base para a proposta, não resultados de validação. Eles mostram o que será implementado e testado na próxima etapa, não algo já concluído."

**"Por que a apresentação não mostra os resultados dos testes?"**
> "Por orientação recebida para esta pré-banca: o professor pediu para desenvolver a apresentação até Materiais e Métodos, já que ainda estamos na etapa de proposta, não de resultados finais. Os resultados experimentais serão apresentados na defesa completa da TCC I."

**"Qual é exatamente o estudo de caso?"**
> "É uma plataforma real de detecção de fraude em transações eletrônicas, com exigências rígidas de SLA e regulatórias — um cenário rico para estudar MLOps em produção. Os diagramas mostrados documentam a arquitetura de referência desse estudo de caso, sobre a qual a proposta se apoia."

**"Qual foi exatamente sua contribuição no projeto, já que o modelo foi feito por outra pessoa?"**
> "Minha autoria é a camada de DevOps/Infraestrutura: infraestrutura como código, orquestração, pipelines de CI/CD e treinamento contínuo, e escalonamento. O modelo de Machine Learning — features e algoritmo — foi construído por outra frente da equipe, de Ciência de Dados. Essa separação de responsabilidades é, inclusive, um dos pontos que o referencial teórico discute como boa prática de MLOps."

**"Por que usar Terraform e KEDA especificamente, e não outras ferramentas?"**
> "Terraform permite versionar a infraestrutura como código e garantir paridade entre ambientes, algo central na literatura de IaC (Karimibiuki et al.). KEDA foi escolhido porque o padrão de carga de sistemas de inferência de ML costuma ser orientado a eventos — filas de mensagens — não apenas a uso de CPU, e a literatura de Kubernetes aponta esse mecanismo como mais aderente a esse tipo de carga."

**"Como será feita a validação experimental, na prática?"**
> "O plano é usar testes de carga com a ferramenta Locust, simulando tráfego real, e comparar o comportamento do sistema sob dois mecanismos de escalonamento — o tradicional, baseado em CPU, e o orientado a eventos, baseado na fila. Os resultados dessa comparação serão o núcleo da próxima etapa do trabalho."

**"O que muda entre esta pré-banca e a apresentação final da TCC I?"**
> "Aqui apresento a proposta: tema, problema, justificativa, objetivos, referencial teórico, metodologia e a arquitetura de referência. Na defesa final da TCC I, apresento a arquitetura efetivamente implementada, os pipelines em funcionamento, e os resultados experimentais já obtidos — com discussão e conclusão."

---

## Resumo de tempo (checkpoints)

| Checkpoint | Tempo alvo | Se estiver atrasado... |
|---|---|---|
| Fim do slide 6 (Objetivos) | ~3:40 | Encurte o slide 3 (Tema) — corte a frase sobre autoria e vá direto à pergunta de pesquisa |
| Fim do slide 7 (Referencial Teórico) | ~4:25 | Cite só o nome do pilar + autor, sem a frase de contexto de cada card |
| Fim do slide 9 (Materiais e Métodos) | ~5:50 | Corte a lista de materiais para só 3 itens (Terraform, EKS, KEDA) |
| Fim do slide 13 (último diagrama) | ~7:30 | Nos slides 10–13, reduza a uma frase ainda mais curta cada — ex.: "esta é a arquitetura de referência proposta" sem repetir detalhes |
| Fim do slide 15 (Referências) | ~8:35 | Cite só 2 referências em vez de 5 |

**Se, mesmo assim, o ensaio mostrar que 10 minutos não são suficientes:** os candidatos a corte adicional, em ordem de prioridade, são: (1) reduzir os 4 slides de diagrama a uma frase única e comum ("estes diagramas documentam a arquitetura proposta para o estudo de caso"), sem uma frase própria por slide; (2) resumir o slide 14 (Cronograma) a uma única frase; (3) no slide 7, citar só 2 dos 4 pilares em detalhe; (4) citar apenas 1 referência no slide 15. Não corte a pergunta de pesquisa (slide 4) nem os objetivos (slide 6) — são o núcleo da proposta.

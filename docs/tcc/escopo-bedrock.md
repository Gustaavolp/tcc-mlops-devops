# Escopo do Componente Bedrock no TCC

Documento de definição do escopo acadêmico do componente `agent_bedrock/` para uso no artigo e na defesa do TCC.

---

## 1. O que o componente realmente faz (análise do código)

O componente `agent_bedrock/` implementa uma **camada de observabilidade generativa** — não um Bedrock Agent conversacional como o nome sugere. Ele é composto por três sub-componentes:

### 1.1. `promotion/` — Lambda `elo-fraud-promotion-reporter`
**Propósito:** Gerar relatórios automáticos de promoção de modelos com linguagem natural.

**Fluxo:**
1. Disparo diário via CloudWatch EventBridge (`cron(0 10 * * ? *)`)
2. Consulta MLflow pelas promoções de modelo nas últimas 240 horas
3. Para cada promoção: coleta métricas do modelo atual (`f1_oot`) e do anterior, informações de dataset, timestamp
4. Monta um payload estruturado e envia ao AWS Bedrock via `bedrock-runtime.invoke_model`
5. O LLM gera dois rascunhos de e-mail em pt-BR:
   - **Técnico:** model name, run_ids, comparação de métricas, dataset
   - **Executivo:** resumo conciso da decisão de promoção
6. Salva o relatório completo (JSON) em S3

**Modelo LLM:** configurável via `BEDROCK_MODEL_ID` — padrão `openai.gpt-oss-120b-1:0` (acesso cross-provider via Bedrock)

### 1.2. `statistics/` — Lambda `elo-fraud-statistics-reporter`
**Propósito:** Monitoramento diário do modelo em produção com relatório em linguagem natural.

**Fluxo:**
1. Disparo diário via CloudWatch EventBridge
2. Consulta Athena com queries sobre a tabela `inference_logs` (últimas N horas, configurável)
3. Calcula: total de transações, score médio, alertas emitidos (PPR), latência P95, distribuição de scores (P50/P90/P95/P99)
4. Compara janela atual com janela anterior (deltas absolutos + percentuais)
5. Busca threshold do modelo no MLflow
6. Chama Bedrock com **3 tentativas encadeadas** (inicial → repair → targeted repair) para garantir JSON válido
7. Salva relatório JSON em S3

**Evidência real de funcionamento** (arquivo `statistics/output.txt`, data 2026-02-19):
```
Janela: 2026-02-18 18:00 até 2026-02-19 18:00
Transações: 19.632
Score médio: 0.000777
Alertas: 4 (PPR 0,0204%)
Threshold: 0.0100
Distribuição: P50 0.000241% | P90 0.010629% | P95 0.047258% | P99 1.535125%
Comparação 24h: volume diminuiu -58,55% | score médio aumentou +233,23%
```

### 1.3. `lambda/` — Coletor de dados para Action Group
**Propósito:** Servir como *action group* de um Bedrock Agent conversacional.

**Fluxo:**
- Recebe eventos no formato Bedrock Agent (`actionGroup`, `apiPath`, `httpMethod`)
- Consulta Athena e MLflow em paralelo
- Retorna os resultados formatados para o Agent no formato esperado pela AWS

**Nota:** O Bedrock Agent em si (recurso `aws_bedrockagent_agent`) **não está provisionado no repositório** — apenas a Lambda de suporte. O Agent provavelmente está configurado via console AWS.

---

## 2. Precisão técnica importante: o que NÃO é esse componente

| Afirmação imprecisa | Realidade |
|---------------------|-----------|
| "É um Bedrock Agent" | É um conjunto de Lambdas que **usam** o Bedrock via `invoke_model`, não um Agent orquestrador |
| "O Bedrock toma decisões" | O Bedrock apenas **formata** relatórios em linguagem natural — todas as decisões (promoção, threshold, comparação) são feitas por código Python determinístico |
| "Há agente conversacional em produção" | O `lambda/` foi desenhado para isso, mas o Agent AWS não está no Terraform do repositório |

---

## 3. Posicionamento no TCC

### 3.1. Enquadramento recomendado

O componente deve ser apresentado no TCC como um **componente de observabilidade com IA generativa**, não como o componente central do pipeline MLOps. É um complemento que eleva a comunicabilidade das métricas operacionais.

**Papel no artigo:**
- Seção 5.1 (Descrição da Abordagem): mencionar brevemente como componente de observabilidade
- Pode ser expandido em uma subseção 5.3 se o orientador aprovar

### 3.2. Texto sugerido para a Seção 5.1

Inserir ao final da descrição da abordagem (após o parágrafo do KEDA):

> "Como camada de observabilidade, o sistema conta com dois relatórios automáticos gerados diariamente via AWS Lambda integrados ao Amazon Bedrock. O *Promotion Reporter* detecta promoções de modelos no MLflow e utiliza um LLM (*Large Language Model*) para redigir notificações em linguagem natural direcionadas tanto à equipe técnica quanto à área executiva, comunicando a justificativa da promoção e a comparação de métricas. O *Statistics Reporter* consulta o Amazon Athena sobre os logs de inferência das últimas 24 horas, calcula métricas operacionais (volume, score médio, taxa de alertas, latência) e gera um relatório comparativo período a período, também redigido pelo LLM em português. Os relatórios são persistidos em S3 e podem ser recuperados ou integrados a sistemas de notificação como Amazon SES."

### 3.3. Posição no diagrama de arquitetura (Task #22)
O componente deve aparecer como:
```
CloudWatch EventBridge
    → Lambda (Promotion Reporter) → MLflow → Bedrock → S3
    → Lambda (Statistics Reporter) → Athena → Bedrock → S3
```
Separado do fluxo principal (API Gateway → EKS → SQS) para não confundir a arquitetura central.

---

## 4. Referência bibliográfica adicional (complemento à Task #17)

Para embasar o uso de IA generativa como ferramenta de comunicação de métricas MLOps, sugere-se adicionar como 16ª referência:

**AMAZON WEB SERVICES (AWS).** *Amazon Bedrock User Guide*. Disponível em: AWS Documentation. Acesso em: jun. 2026.

> **Onde citar:** Seção 5.1 ou 5.3 ao mencionar o componente Bedrock, assim como no referencial teórico se uma subseção for aberta para "IA Generativa em MLOps".
>
> **Sugestão de frase:** *"O Amazon Bedrock é um serviço gerenciado da AWS que disponibiliza modelos de linguagem de grande escala (LLMs) de múltiplos provedores via API unificada, eliminando a necessidade de provisionamento de infraestrutura de inferência (AWS, 2026)."*

---

## 5. Limitações e decisões de escopo a declarar no TCC

1. **Modelo LLM configurável:** A implementação suporta modelos LLaMA e OpenAI via Bedrock. Nos testes documentados (`output.txt`), o modelo utilizado foi o `openai.gpt-oss-120b-1:0`.
2. **Sem persistência de conversação:** O componente não implementa histórico de sessão — cada invocação é stateless.
3. **Sem Bedrock Agent em produção:** O `lambda/` foi projetado como action group mas o Bedrock Agent orquestrador não foi finalizado dentro do escopo do projeto.
4. **Foco em comunicação, não em decisão:** O LLM não participa das decisões de promoção ou treinamento — apenas as descreve em linguagem natural.

---

## 6. Resumo executivo do escopo

> O componente `agent_bedrock/` implementa **observabilidade com linguagem natural**: recebe dados estruturados de MLflow e Athena, e usa um LLM via Amazon Bedrock para traduzir métricas operacionais em relatórios legíveis por humanos. É um componente de **comunicação**, não de **decisão**. Seu valor acadêmico está na demonstração de como IA generativa pode ser integrada ao ciclo MLOps para reduzir o esforço de comunicação entre times técnicos e de negócio.

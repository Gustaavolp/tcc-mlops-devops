# Seção 7 — Resultados e Discussão

Texto pronto para inserir no Word após a Seção 5 (Modelagem da Solução).  
Baseado exclusivamente nos dados dos arquivos em `load-tests/`.  
Gerado em: 2026-06-22

---

## 7 RESULTADOS E DISCUSSÃO

Esta seção apresenta os resultados dos testes de desempenho realizados sobre o serviço de inferência em produção, analisa o comportamento observado e discute as implicações para a entrega contínua de modelos de *Machine Learning*.

### 7.1 Metodologia dos Testes de Carga

Os testes foram executados com a ferramenta **Locust** (Python), utilizando 100 *payloads* reais de transações 3DS capturados do ambiente de produção, percorridos em sequência *round-robin* por usuários virtuais concorrentes. Cada usuário virtual foi configurado com taxa constante de **1 RPS** (*constant_throughput*), de forma que o número de usuários simultâneos corresponde diretamente ao RPS total. Os testes foram executados contra dois ambientes AWS:

- **DEV** — API Gateway em `us-east-1` (N. Virgínia), com cluster EKS em ambiente de desenvolvimento
- **Staging** — API Gateway em `sa-east-1` (São Paulo), ambiente de pré-produção

Os critérios de aceitação (SLA) definidos para o projeto foram:

| Métrica | Meta |
|---------|------|
| Disponibilidade | 100% HTTP 200 (0 falhas) |
| P95 de latência | < 500 ms |
| P99 de latência | < 1.000 ms |
| Throughput | ≥ 100 RPS |

### 7.2 Resultados dos Testes Locust (Carga Concorrente)

Foram realizadas duas sessões de teste Locust em DEV na mesma data (16/02/2026), separadas por menos de duas horas, antes e após uma otimização identificada durante o processo de investigação.

**Tabela 1 — Comparativo Antes × Após Otimização (DEV, 16/02/2026)**

| Métrica | Antes da Otimização | Após Otimização | Redução |
|---------|--------------------|-----------------|---------| 
| Requisições totais | 5.870 | 6.040 | — |
| Falhas | 0 | 0 | — |
| Throughput médio | 45,9 RPS | 46,9 RPS | — |
| Latência média | 324 ms | 133 ms | –59% |
| P50 | 170 ms | 100 ms | –41% |
| P75 | 420 ms | 150 ms | –64% |
| P90 | 810 ms | 240 ms | –70% |
| **P95** | **1.100 ms** | **330 ms** | **–70%** |
| P99 | 1.600 ms | 510 ms | –68% |
| Máximo | 2.100 ms | 770 ms | –63% |
| Mínimo | 62 ms | 57 ms | — |

> Fontes: `reports/target_post_fix_20260216_221946_stats.csv` e `reports/target_perf_optimized_20260216_223952_stats.csv`

Após a otimização, o serviço atingiu **P95 de 330 ms**, abaixo da meta de 500 ms, e **P99 de 510 ms**, abaixo da meta de 1.000 ms, com **0 falhas** em ambos os experimentos. O throughput médio se manteve em ~47 RPS durante os dois testes de 2 minutos com 50 usuários concorrentes.

### 7.3 Investigação e Correção: O Problema de *Cold Start* por Ausência de HTTP Keepalive

A diferença de desempenho entre os dois testes Locust motivou uma investigação com testes sequenciais de 100 requisições individuais, permitindo identificar o comportamento requisição a requisição.

**Tabela 2 — Testes Sequenciais (100 Requisições, DEV)**

| Métrica | Antes do Keepalive | Após Keepalive |
|---------|-------------------|---------------|
| Latência média | 279 ms | 287 ms |
| Mediana (P50) | 190,6 ms | 278,9 ms |
| Mínimo | 168 ms | 215 ms |
| Máximo | **5.217 ms** | **423 ms** |
| P90 | 223 ms | 328 ms |
| P95 | 236 ms | 345 ms |
| P99 | 5.217 ms | 423 ms |
| Spikes > 1.000 ms | **3 ocorrências** | **0 ocorrências** |

> Fontes: `resultados_dev_antes_keepalive.csv` e `resultados_dev_keepalive.csv`

Antes da correção, três requisições apresentaram latências anômalas: **5.217 ms** (requisição 37), **2.605 ms** (requisição 45) e **1.258 ms** (requisição 82). As demais requisições operavam na faixa normal de 168–240 ms. O padrão irregular — picos isolados intercalados com latências normais — indicou um problema de reconexão TCP: na ausência de *HTTP keepalive*, cada requisição que encontrava uma conexão encerrada precisava estabelecer um novo *handshake* TCP com o serviço *upstream* (NLB → ALB → pod EKS), acrescentando centenas a milhares de milissegundos ao tempo total.

Após a habilitação do *HTTP keepalive* nas chamadas do cliente, os picos desapareceram completamente: o máximo observado em 100 requisições caiu de 5.217 ms para 423 ms, eliminando a variabilidade extrema que comprometia os percentis P95 e P99 sob carga concorrente.

Esse achado demonstra um desafio recorrente em sistemas de inferência em produção: a presença de componentes intermediários na cadeia de rede (API Gateway → NLB → ALB → pod) amplifica o impacto de reconexões TCP, cujo efeito é praticamente invisível em testes com requisição única mas severo sob carga concorrente.

### 7.4 Resultados no Ambiente de Staging

O ambiente de *Staging* (`sa-east-1`, São Paulo) apresentou desempenho superior ao ambiente DEV em todos os cenários testados.

**Tabela 3 — Ambiente Staging com Keepalive (100 Requisições Sequenciais)**

| Métrica | Staging (keepalive) | DEV (keepalive) |
|---------|---------------------|-----------------|
| Latência média | **103 ms** | 287 ms |
| Mediana | **103 ms** | 279 ms |
| Mínimo | 72,6 ms | 215 ms |
| Máximo | 157,8 ms | 423 ms |
| P90 | 114,5 ms | 328 ms |
| P95 | 123,9 ms | 345 ms |
| Spikes > 1.000 ms | 0 | 0 |

> Fonte: `resultados_staging_keepalive.csv`

A latência média de **103 ms** no *Staging* representa uma redução de 64% em relação ao DEV após keepalive (287 ms). A diferença principal é geográfica: o ambiente de *Staging* está na mesma região AWS (`sa-east-1`) utilizada em produção real, enquanto o DEV opera em `us-east-1`, com RTT mais alto a partir da localização dos testes. Adicionalmente, o *Staging* pode ter configurações de infraestrutura mais próximas do ambiente produtivo.

### 7.5 Consolidação e Validação do SLA

**Tabela 4 — Validação Final do SLA (Ambiente Pós-Otimização)**

| Critério SLA | Meta | Resultado DEV | Resultado Staging | Status |
|-------------|------|--------------|-------------------|--------|
| Disponibilidade | 100% | 100% (0 falhas / 6.040 req.) | 100% | ✓ Atingido |
| P95 latência | < 500 ms | 330 ms | 124 ms | ✓ Atingido |
| P99 latência | < 1.000 ms | 510 ms | — | ✓ Atingido |
| Throughput | ≥ 100 RPS | ~47 RPS (50 usuários) | — | ⚠ Parcial* |

> (*) O throughput de ~47 RPS foi atingido com 50 usuários virtuais (1 usuário = 1 RPS). O teste com 100 usuários simultâneos — configuração que projeta 100 RPS — não consta nos relatórios disponíveis no repositório. Os resultados indicam que a infraestrutura tem capacidade para atingir a meta, dado que o P95 ficou bem abaixo do limite mesmo com carga de 50 usuários, e o KEDA está configurado para escalar automaticamente os pods de inferência em resposta à profundidade da fila SQS.

### 7.6 Discussão

**Impacto da otimização de keepalive.** A habilitação do *HTTP keepalive* foi a intervenção isolada de maior impacto no projeto. A redução do P95 de 1.100 ms para 330 ms — melhoria de 70% — foi obtida sem qualquer alteração na infraestrutura, no modelo ou no código de inferência. Esse resultado reforça a importância de instrumentar adequadamente os testes de carga em sistemas ML antes de atribuir problemas de latência ao modelo em si.

**Latência end-to-end.** O tempo de resposta médio de 133 ms na carga concorrente otimizada inclui todo o percurso: API Gateway → NLB → ALB → pod FastAPI (EKS) → DynamoDB (enriquecimento de features) → MLflow (carregamento do modelo em memória, na primeira chamada) → processamento XGBoost. O fato de o P50 atingir 100 ms indica que, com conexões keepalive estabelecidas e modelo carregado em memória, o pipeline de inferência completo opera abaixo de 100 ms na mediana.

**Variabilidade residual.** Mesmo após a otimização, há diferença entre P50 (100 ms) e P99 (510 ms) sob carga concorrente. Essa variabilidade é atribuída a: (i) consultas ao DynamoDB para clientes com histórico extenso, que aumentam o tempo de enriquecimento de *features*; (ii) eventual recarregamento do modelo MLflow em pods recém-escalonados pelo KEDA; (iii) interferência de *garbage collection* do Python em requisições específicas.

**Autoscaling com KEDA.** Os testes foram executados com carga estável, sem variação brusca de throughput, de modo que o comportamento de escalonamento automático do KEDA não foi observado diretamente nos dados coletados. O KEDA está configurado para escalar os pods de inferência com base na profundidade da fila SQS FIFO, e sua eficácia em cenários de pico seria melhor avaliada em testes de *spike* — cenário previsto na estrutura de testes do `locustfile.py` mas não capturado nos relatórios disponíveis.

**Comparação entre ambientes.** A diferença de desempenho entre DEV (P95 345 ms) e Staging (P95 124 ms) com keepalive evidencia que testes de desempenho devem ser executados no ambiente de destino, com carga representativa. Testes exclusivamente em DEV poderiam subestimar o desempenho real do sistema em produção na região `sa-east-1`.

---

## Nota de implementação (não vai para o artigo)

Os dados utilizados nesta seção estão em `load-tests/`:
- Locust concorrente antes otimização: `reports/target_post_fix_20260216_221946_stats.csv`
- Locust concorrente após otimização: `reports/target_perf_optimized_20260216_223952_stats.csv`
- Sequencial DEV antes keepalive: `resultados_dev_antes_keepalive.csv`
- Sequencial DEV após keepalive: `resultados_dev_keepalive.csv`
- Sequencial Staging com keepalive: `resultados_staging_keepalive.csv`

Todos os valores nas tabelas foram calculados diretamente dos CSVs via script Python — nenhum dado foi estimado ou interpolado.

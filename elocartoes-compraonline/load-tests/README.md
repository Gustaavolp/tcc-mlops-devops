# Load Tests - Elo Fraud Detection API

Testes de carga para validar a meta de **100 RPS com p95 < 500ms**.

## Execução Rápida

```bash
# Entrar no diretório
cd load-tests

# Smoke test (validação básica)
./run_tests.sh smoke

# Target 100 RPS (meta principal)
./run_tests.sh target

# Interface web interativa
./run_tests.sh web
```

## Instalação

```bash
cd load-tests

# Opção 1: pip direto
pip install locust

# Opção 2: virtualenv (recomendado)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Cenários de Teste

| Cenário | Comando | Usuários | Duração | Objetivo |
|---------|---------|----------|---------|----------|
| **Smoke** | `./run_tests.sh smoke` | 5 | 30s | Validação básica |
| **Load** | `./run_tests.sh load` | 20 | 2min | Carga normal |
| **Target** | `./run_tests.sh target` | 50 | 2min | **100 RPS com p95 < 500ms** |
| **Stress** | `./run_tests.sh stress` | 100 | 5min | Encontrar limite |
| **Spike** | `./run_tests.sh spike` | 200 | 1min | Pico súbito |
| **Ramp-up** | `./run_tests.sh rampup` | 10→100 | 3min | Ramp-up gradual |
| **Web** | `./run_tests.sh web` | - | - | Interface interativa |

## Fórmula para Calcular Usuários

```
usuarios_necessarios = target_rps × latencia_media_segundos
```

Exemplos:
- **100 RPS com 300ms de latência**: 100 × 0.3 = **30 usuários**
- **100 RPS com 500ms de latência**: 100 × 0.5 = **50 usuários**
- **200 RPS com 300ms de latência**: 200 × 0.3 = **60 usuários**

## Ambientes

| Ambiente | URL | Região |
|----------|-----|--------|
| **Staging** (default) | `https://td5i6sx8rh.execute-api.sa-east-1.amazonaws.com` | São Paulo |
| Dev | `https://oc9dm394cf.execute-api.us-east-1.amazonaws.com` | N. Virginia |

## Métricas de Sucesso (SLA)

| Métrica | Target | Descrição |
|---------|--------|-----------|
| **RPS** | ≥ 100 | Requisições por segundo |
| **p95** | < 500ms | 95% das requisições abaixo desse tempo |
| **p99** | < 1000ms | 99% das requisições abaixo desse tempo |
| **Erros** | < 1% | Taxa de erro máxima |

## Execução Manual com Locust

```bash
# Básico
locust -f locustfile.py --headless -u 50 -r 10 -t 2m

# Com relatório HTML
locust -f locustfile.py --headless -u 50 -r 10 -t 2m --html report.html

# Parâmetros
#   -u  : Número de usuários simultâneos
#   -r  : Spawn rate (usuários/segundo)
#   -t  : Duração (30s, 2m, 5m, etc.)
#   --html : Gerar relatório HTML
#   --csv  : Gerar relatório CSV
```

## Estrutura dos Testes

```
load-tests/
├── locustfile.py      # Arquivo principal de testes
├── run_tests.sh       # Script de execução simplificado
├── requirements.txt   # Dependências Python
├── README.md          # Esta documentação
└── reports/           # Relatórios gerados (HTML, CSV)
```

## Mix de Cenários

O teste usa um mix de cenários para simular tráfego real:

| Cenário | Peso | Descrição |
|---------|------|-----------|
| Usuário novo | 70% | Sem histórico no DynamoDB (cold start) |
| Usuário conhecido | 30% | Com histórico (enriquecimento de features) |

## Interpretando os Resultados

### Exemplo de Output

```
============================================================
RESULTADOS DO TESTE
============================================================
Total Requests:  12000
Duração:         120.5s
RPS:             99.6

Latência (ms):
  Min:           45.2
  Avg:           287.3
  Median:        265.1
  P95:           489.5
  P99:           756.2
  Max:           1234.5

Erros:           12 (0.1%)

✓ SLA ATINGIDO: p95 < 500ms
✓ TARGET RPS ATINGIDO: 99.6 >= 100
============================================================
```

### Relatório HTML

Os relatórios HTML gerados incluem:
- Gráfico de RPS ao longo do tempo
- Gráfico de latência (avg, p50, p95, p99)
- Gráfico de erros
- Tabela de estatísticas por endpoint

## Troubleshooting

### Baixo RPS

Se não está atingindo o RPS desejado:

1. **Aumentar usuários**: Cada usuário faz ~10 RPS (se latência for baixa)
2. **Verificar infraestrutura**: HPA, pods, nodes podem estar limitando
3. **Verificar throttling**: API Gateway pode ter rate limit

### Latência Alta

Se o p95 está acima de 500ms:

1. **Cold start de pods**: Primeiras requisições são lentas
2. **DynamoDB**: Consulta de histórico pode estar lenta
3. **Modelo ML**: Inferência pode estar lenta
4. **Escala insuficiente**: HPA pode não ter escalado ainda

### Erros 429 (Too Many Requests)

- API Gateway tem rate limiting configurado
- Reduza o spawn rate ou número de usuários
- Verifique quotas do AWS API Gateway

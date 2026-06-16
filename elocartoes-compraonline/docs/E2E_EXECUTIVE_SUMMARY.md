# Resumo Executivo - Testes E2E Elo Fraud Detection

> **Reuniao de Testes End-to-End**
> **Data**: 2026-01-16
> **Ambiente**: DEV (us-east-1)
> **Responsavel DevOps**: Gustavo Liebl Pereira

---

## Status do Sistema

| Componente | Status | Observacao |
|------------|--------|------------|
| EKS Cluster | **ATIVO** | v1.32 |
| Inference Service | **OPERACIONAL** | 2 pods rodando |
| Process Worker | **OPERACIONAL** | 1 pod rodando |
| ALB | **ATIVO** | Health check OK |
| API Gateway | **ATIVO** | Stage v1 |
| DynamoDB | **ATIVO** | 4.6M registros |
| SQS | **ATIVO** | Fila vazia |
| Firehose | **ATIVO** | 2 streams |

---

## Endpoints para Teste

```
# Health Check
GET http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health

# Scoring (Principal)
POST http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score
```

---

## Teste Rapido

```bash
# 1. Health Check
curl -s http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health

# 2. Scoring
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "E2E-TEST-001",
    "cardHolderDocument": "12345678901",
    "amount": "150.00",
    "cd_merchant_category_code": "5411",
    "cd_merchant_country": "BRA"
  }'
```

**Resposta Esperada:**
```json
{
  "transaction_id": "E2E-TEST-001",
  "score": 0.23,
  "fraud_label": 0
}
```

---

## SLA e Metricas

| Metrica | Target | Como Medir |
|---------|--------|------------|
| Latencia p95 | **< 500ms** | `curl -w "%{time_total}s"` |
| Disponibilidade | 99.9% | Health check |
| Taxa de Erro | < 0.1% | HTTP 2xx vs 5xx |

---

## Fluxo de Dados

```
Cliente Elo
    │
    ▼
┌─────────────┐
│ API Gateway │ → Rate limit: 10k/s
└─────────────┘
    │
    ▼
┌─────────────┐
│     ALB     │ → Health check: /health
└─────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│           EKS (fraud-detection)         │
│                                         │
│  ┌─────────────┐     ┌─────────────┐    │
│  │  Inference  │ ──► │    SQS      │    │
│  │  (2 pods)   │     │   (FIFO)    │    │
│  └─────────────┘     └─────────────┘    │
│         │                   │           │
│         ▼                   ▼           │
│  ┌─────────────┐     ┌─────────────┐    │
│  │  DynamoDB   │     │   Process   │    │
│  │ (features)  │     │  (1 pod)    │    │
│  └─────────────┘     └─────────────┘    │
│                             │           │
│                             ▼           │
│                      ┌─────────────┐    │
│                      │  Firehose   │    │
│                      │   → S3      │    │
│                      └─────────────┘    │
└─────────────────────────────────────────┘
```

---

## Documentacao Disponivel

| Documento | Conteudo |
|-----------|----------|
| [E2E_TESTING_GUIDE.md](./E2E_TESTING_GUIDE.md) | Guia completo de testes com passo a passo |
| [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md) | Arquitetura e configuracoes detalhadas |
| [PAYLOAD_REFERENCE.md](./PAYLOAD_REFERENCE.md) | Exemplos de payloads e medicao de tempo |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Diagnostico de problemas e comandos uteis |

---

## Comandos Uteis Durante a Reuniao

```bash
# Monitor de pods
watch -n 2 kubectl get pods -n fraud-detection

# Logs em tempo real
kubectl logs -f -n fraud-detection deployment/inference

# Status SQS
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1

# Teste de latencia
curl -X POST http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TEST","cardHolderDocument":"123","amount":"100","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}' \
  -w "\nTempo: %{time_total}s\n"
```

---

## Checklist Pre-Reuniao

- [ ] EKS Cluster ativo
- [ ] 2+ pods inference rodando
- [ ] 1+ pod process rodando
- [ ] Health check retorna 200
- [ ] SQS sem mensagens pendentes
- [ ] DLQ vazia
- [ ] DynamoDB acessivel
- [ ] Firehose ativo

---

## Pontos de Atencao

1. **MLflow Stopped**: Tracking server parado, modelo carregado localmente na imagem
2. **Single NAT**: Apenas 1 NAT Gateway (nao HA)
3. **IRSA Desabilitado**: Pods usam Node IAM Role

---

## Contatos

| Area | Responsavel |
|------|-------------|
| DevOps/Infra | Gustavo Liebl Pereira |
| ML/Data Science | Ana/Vinicios |
| Dados 3DS | Denis |

---

*Documento gerado em 2026-01-15*

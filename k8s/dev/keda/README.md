# KEDA - Kubernetes Event-Driven Autoscaling (DEV)

Configuracao KEDA para auto-scaling do worker process baseado na profundidade da fila SQS.

## Arquivos

| Arquivo | Recurso | Descricao |
|---------|---------|-----------|
| `process-scaledobject.yaml` | ScaledObject | Auto-scaling do process baseado em SQS |

## O que e KEDA

KEDA (Kubernetes Event-Driven Autoscaling) permite escalar workloads baseado em eventos externos, como numero de mensagens em uma fila SQS.

```
SQS Queue ──► KEDA Operator ──► ScaledObject ──► Deployment (process)
   │                                                    │
   └── Mensagens na fila ──────────────────────────────► Replicas
```

## Configuracoes

### ScaledObject

| Configuracao | Valor |
|--------------|-------|
| Namespace | `fraud-detection` |
| Target | Deployment `process` |
| Min Replicas | 1 |
| Max Replicas | 5 |

**Trigger SQS:**

| Configuracao | Valor |
|--------------|-------|
| Tipo | `aws-sqs-queue` |
| Queue URL | `https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo` |
| Queue Length | 30 mensagens por pod |
| AWS Region | us-east-1 |
| Identity Owner | operator |

**Intervalos:**

| Configuracao | Valor | Descricao |
|--------------|-------|-----------|
| Polling Interval | 15s | Frequencia de verificacao da fila |
| Cooldown Period | 60s | Tempo antes de permitir scale down |

**Comportamento de Scaling:**

| Acao | Configuracao | Descricao |
|------|--------------|-----------|
| Scale-up | Imediato | Sem janela de estabilizacao |
| Scale-up Rate | 1 pod / 15s | Adiciona 1 pod por ciclo |
| Scale-down | 120s | Janela de estabilizacao |
| Scale-down Rate | 1 pod / 60s | Remove 1 pod por minuto |

## Logica de Scaling

| Mensagens na Fila | Replicas |
|-------------------|----------|
| 0 | 1 (minimo) |
| 1-30 | 1 |
| 31-60 | 2 |
| 61-90 | 3 |
| 91-120 | 4 |
| 121+ | 5 (maximo) |

## Pre-requisitos

| Componente | Descricao |
|------------|-----------|
| KEDA Operator | Instalado no cluster via Helm |
| IAM Permissions | Node role com permissao `sqs:GetQueueAttributes` |
| SQS Queue | Fila FIFO criada pelo Terraform |

## Vantagens sobre HPA

| Aspecto | HPA Tradicional | KEDA |
|---------|-----------------|------|
| Metrica | CPU/Memory | Mensagens na fila |
| Escala para zero | Nao | Sim (se configurado) |
| Reatividade | Baseado em carga | Baseado em demanda real |
| Custo | Pods sempre rodando | Pods sob demanda |

## Dependencias

| Recurso | Namespace | Tipo |
|---------|-----------|------|
| `process` | fraud-detection | Deployment |
| KEDA Operator | keda | Deployment |

## Gerenciamento

Este manifest e gerenciado via `kubectl apply`. Para alteracoes, edite o arquivo YAML e aplique:

```bash
kubectl apply -f k8s/dev/keda/process-scaledobject.yaml
```

## Comandos Uteis

```bash
# Verificar ScaledObject
kubectl get scaledobject -n fraud-detection

# Descrever ScaledObject
kubectl describe scaledobject process-scaledobject -n fraud-detection

# Verificar HPA gerado pelo KEDA
kubectl get hpa -n fraud-detection

# Verificar metricas do KEDA
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/fraud-detection/s0-aws-sqs-queue-elo-fraud-transactions-dev"

# Verificar logs do KEDA operator
kubectl logs -n keda -l app=keda-operator --tail=100

# Verificar status do deployment escalado
kubectl get deployment process -n fraud-detection
```

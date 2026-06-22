# Process Service - Kubernetes Manifests (DEV)

Manifests Kubernetes para o worker de processamento de transacoes no ambiente de desenvolvimento.

## Arquivos

| Arquivo | Recurso | Descricao |
|---------|---------|-----------|
| `deployment.yaml` | Deployment | Pod do worker SQS |
| `configmap.yaml` | ConfigMap | Variaveis de ambiente (SQS, DynamoDB, S3, Firehose) |
| `pdb.yaml` | PodDisruptionBudget | Garantia de disponibilidade durante manutencoes |

## Arquitetura

```
SQS FIFO ──► Pod (process)
                  │
                  ├──► DynamoDB (atualiza fraud_label)
                  │
                  └──► S3 (persiste historico)
```

## Configuracoes

### Deployment

| Configuracao | Valor |
|--------------|-------|
| Namespace | `fraud-detection` |
| Replicas | 1 |
| Imagem | `888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-process-dev:latest` |
| ServiceAccount | `process-service` |

**Recursos do Container:**

| Tipo | CPU | Memoria |
|------|-----|---------|
| Request | 100m | 256Mi |
| Limit | 500m | 512Mi |

**Estrategia de Deploy:**

| Configuracao | Valor | Descricao |
|--------------|-------|-----------|
| Strategy | RollingUpdate | Deploy sem perda de mensagens |
| maxSurge | 1 | Cria 1 pod extra durante update |
| maxUnavailable | 0 | Nunca remove pods ate novo estar ready |

## Health Probes

O worker **nao possui health probes HTTP** porque:

| Razao | Descricao |
|-------|-----------|
| Sem endpoint HTTP | Worker nao expoe servidor web |
| Restart automatico | Kubernetes reinicia se processo crashar |
| Long polling | Processo fica bloqueado esperando SQS (comportamento normal) |

## Seguranca

| Aspecto | Configuracao |
|---------|--------------|
| runAsNonRoot | true |
| runAsUser | 1000 |
| fsGroup | 1000 |

## Afinidade de Pods

| Tipo | Comportamento |
|------|---------------|
| Pod Anti-affinity | Distribui replicas entre nodes diferentes |
| Node Affinity | Prefere nodes com label `role=general` |

## Variaveis de Ambiente

**Via ConfigMap (`process-config`):**

Configuracoes de aplicacao injetadas pelo ConfigMap.

**Via Downward API:**

| Variavel | Descricao |
|----------|-----------|
| `POD_NAME` | Nome do pod |
| `POD_NAMESPACE` | Namespace do pod |
| `POD_IP` | IP do pod |
| `NODE_NAME` | Nome do node |

## Graceful Shutdown

| Fase | Duracao | Acao |
|------|---------|------|
| preStop | 10s | Sleep para finalizar processamento atual |
| terminationGracePeriod | 60s | Tempo total para encerramento |

O grace period de 60s permite:
- Finalizar processamento do batch atual
- Mensagens nao deletadas retornam a fila automaticamente

## Dependencias

| Recurso | Namespace | Tipo |
|---------|-----------|------|
| `process-config` | fraud-detection | ConfigMap |
| `process-service` | fraud-detection | ServiceAccount |

## Integracao AWS

| Servico | Operacao |
|---------|----------|
| SQS | ReceiveMessage, DeleteMessage |
| DynamoDB | UpdateItem |
| S3 | PutObject |
| ECR | Pull da imagem |

## Auto-Scaling

O process e escalado pelo **KEDA** baseado na profundidade da fila SQS.

Ver configuracao em: [`../keda/process-scaledobject.yaml`](../keda/)

| Configuracao | Valor |
|--------------|-------|
| Min/Max Replicas | 1-5 |
| Queue Length | 30 msgs/pod |
| Polling Interval | 15s |

## Diferencas do Inference

| Aspecto | Inference | Process |
|---------|-----------|---------|
| Tipo | API HTTP | Worker SQS |
| Probes | Startup, Liveness, Readiness | Nenhum |
| Service | ClusterIP | Nao necessario |
| Auto-scaling | HPA (CPU-based) | KEDA (SQS-based) |
| Grace Period | 30s | 60s |

## Comandos Uteis

```bash
# Verificar status do deployment
kubectl get deployment process -n fraud-detection

# Verificar pods
kubectl get pods -n fraud-detection -l app=process

# Verificar logs
kubectl logs -n fraud-detection -l app=process --tail=100 -f

# Descrever deployment
kubectl describe deployment process -n fraud-detection

# Restart do deployment
kubectl rollout restart deployment/process -n fraud-detection

# Verificar status do rollout
kubectl rollout status deployment/process -n fraud-detection

# Escalar manualmente (se necessario)
kubectl scale deployment/process -n fraud-detection --replicas=2
```

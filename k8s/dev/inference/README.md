# Inference Service - Kubernetes Manifests (DEV)

Manifests Kubernetes para o serviço de inferência de detecção de fraude no ambiente de desenvolvimento.

## Arquivos

| Arquivo | Recurso | Descrição |
|---------|---------|-----------|
| `deployment.yaml` | Deployment | Pods, containers, probes e recursos |
| `service.yaml` | Service (ClusterIP) | Exposição interna no cluster |
| `configmap.yaml` | ConfigMap | Variaveis de ambiente (DynamoDB, SQS, MLflow) |
| `hpa.yaml` | HorizontalPodAutoscaler | Auto-scaling baseado em CPU e memória |
| `pdb.yaml` | PodDisruptionBudget | Garantia de disponibilidade durante manutencoes |
| `target-group-binding.yaml` | TargetGroupBinding | Registro de pods no NLB Target Group |

## Arquitetura

```
API Gateway ──► NLB ──► Service ──► Pod (inference)
                                                   │
                                                   ├──► DynamoDB (histórico)
                                                   │
                                                   └──► SageMaker (scoring ML)
```

## Configuracoes

### Deployment

| Configuracao | Valor |
|--------------|-------|
| Namespace | `fraud-detection` |
| Replicas | 2 |
| Imagem | `888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest` |
| Porta | 8000 |
| ServiceAccount | `inference-service` |

**Recursos do Container:**

| Tipo | CPU | Memoria |
|------|-----|---------|
| Request | 500m | 512Mi |
| Limit | 1000m | 1Gi |

**Health Probes:**

| Probe | Endpoint | Delay Inicial | Intervalo | Timeout | Falhas |
|-------|----------|---------------|-----------|---------|--------|
| Startup | `/health` | 30s | 10s | 5s | 18 |
| Liveness | `/health` | 60s | 30s | 5s | 3 |
| Readiness | `/health` | 10s | 10s | 3s | 2 |

**Estrategia de Deploy:**

| Configuracao | Valor | Descricao |
|--------------|-------|-----------|
| Strategy | RollingUpdate | Deploy sem downtime |
| maxSurge | 1 | Cria 1 pod extra durante update |
| maxUnavailable | 0 | Nunca remove pods ate novo estar ready |

### Service

| Configuracao | Valor |
|--------------|-------|
| Type | ClusterIP |
| Port | 8000 |
| Target Port | 8000 |
| Selector | `app: inference` |

### HPA (HorizontalPodAutoscaler)

| Configuracao | Valor |
|--------------|-------|
| Min Replicas | 2 |
| Max Replicas | 6 |
| Target CPU | 50% |
| Target Memory | 75% |

**Comportamento de Scaling:**

| Acao | Configuracao | Descricao |
|------|--------------|-----------|
| Scale-up | Imediato | Sem janela de estabilizacao |
| Scale-down | 300s | Janela de estabilizacao conservadora |

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

**Via ConfigMap (`inference-config`):**

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
| preStop | 5s | Sleep para drenar conexoes |
| terminationGracePeriod | 30s | Tempo total para encerramento |

## Dependencias

| Recurso | Namespace | Tipo |
|---------|-----------|------|
| `inference-config` | fraud-detection | ConfigMap |
| `inference-service` | fraud-detection | ServiceAccount |

## Comandos Uteis

```bash
# Verificar status do deployment
kubectl get deployment inference -n fraud-detection

# Verificar pods
kubectl get pods -n fraud-detection -l app=inference

# Verificar logs
kubectl logs -n fraud-detection -l app=inference --tail=100

# Verificar HPA
kubectl get hpa inference-hpa -n fraud-detection

# Descrever deployment
kubectl describe deployment inference -n fraud-detection

# Restart do deployment
kubectl rollout restart deployment/inference -n fraud-detection

# Verificar status do rollout
kubectl rollout status deployment/inference -n fraud-detection
```

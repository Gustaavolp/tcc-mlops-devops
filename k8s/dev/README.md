# Kubernetes Manifests - Ambiente DEV

Manifests Kubernetes para o ambiente de desenvolvimento do sistema de detecao de fraude.

## Estrutura

```
dev/
├── resource-quota.yaml             # ResourceQuota + LimitRange
├── serviceaccount-inference.yaml   # ServiceAccount + RBAC inference
├── serviceaccount-process.yaml     # ServiceAccount + RBAC process
├── inference/                      # Manifests do servico inference
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml              # ConfigMap (env vars)
│   ├── hpa.yaml                    # HorizontalPodAutoscaler
│   ├── pdb.yaml                    # PodDisruptionBudget
│   └── target-group-binding.yaml   # TargetGroupBinding (NLB)
├── process/                        # Manifests do servico process
│   ├── deployment.yaml
│   ├── configmap.yaml              # ConfigMap (env vars)
│   └── pdb.yaml                    # PodDisruptionBudget
└── keda/                           # Auto-scaling baseado em eventos
    └── process-scaledobject.yaml
```

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Namespace: fraud-detection                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │           INFERENCE             │  │            PROCESS              │  │
│  │                                 │  │                                 │  │
│  │  ALB ──► Service ──► Deployment │  │  SQS ──► Deployment             │  │
│  │                         │       │  │               │                 │  │
│  │                        HPA      │  │             KEDA                │  │
│  │                         │       │  │               │                 │  │
│  │              DynamoDB + SageMaker│  │        DynamoDB + S3            │  │
│  │                                 │  │                                 │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Servicos

| Servico | Tipo | Descricao |
|---------|------|-----------|
| **inference** | API HTTP | Scoring de fraude em tempo real |
| **process** | Worker SQS | Processamento assincrono de feedback |

## Recursos Base

### Resource Quota (`resource-quota.yaml`)

| Recurso | Descricao |
|---------|-----------|
| ResourceQuota | Limites totais do namespace |
| LimitRange | Defaults para containers |

> **Nota:** O namespace `fraud-detection` e criado pelo Terraform (stack platform-k8s).

### ResourceQuota

| Recurso | Limite |
|---------|--------|
| CPU requests | 4 cores |
| CPU limits | 8 cores |
| Memory requests | 8Gi |
| Memory limits | 16Gi |
| Pods | 20 |
| Services | 10 |
| ConfigMaps | 20 |
| Secrets | 20 |
| PVCs | 5 |

### LimitRange

Defaults para containers sem especificacao:

| Tipo | Request | Limit |
|------|---------|-------|
| CPU | 100m | 500m |
| Memory | 128Mi | 512Mi |

## ServiceAccounts

### inference-service (`serviceaccount-inference.yaml`)

| Recurso | Descricao |
|---------|-----------|
| ServiceAccount | Identidade para pods inference |
| Role | ConfigMaps, Secrets, Events |
| RoleBinding | Liga Role ao ServiceAccount |

**Permissoes AWS (via Node Role):**
- AmazonDynamoDBFullAccess
- AmazonSageMakerFullAccess
- AmazonS3ReadOnlyAccess

### process-service (`serviceaccount-process.yaml`)

| Recurso | Descricao |
|---------|-----------|
| ServiceAccount | Identidade para pods process |
| Role | ConfigMaps, Secrets, Events, Leases |
| RoleBinding | Liga Role ao ServiceAccount |

**Permissoes AWS (via Node Role):**
- AmazonSQSFullAccess
- AmazonDynamoDBFullAccess
- AmazonS3FullAccess

## Subpastas

| Pasta | Descricao |
|-------|-----------|
| [inference/](inference/) | API de scoring em tempo real |
| [process/](process/) | Worker de processamento SQS |
| [keda/](keda/) | Auto-scaling baseado em eventos |

## Recursos por Servico

| Servico | Replicas | CPU Req | CPU Lim | Mem Req | Mem Lim |
|---------|----------|---------|---------|---------|---------|
| inference | 2 (HPA: 2-6) | 500m | 1000m | 512Mi | 1Gi |
| process | 1 (KEDA: 1-5) | 100m | 500m | 256Mi | 512Mi |

## Seguranca

| Aspecto | Configuracao |
|---------|--------------|
| runAsNonRoot | true |
| runAsUser | 1000 |
| fsGroup | 1000 |
| RBAC | Roles limitadas por namespace |
| AWS Auth | Node IAM Role |

## Ordem de Aplicacao

```bash
# 1. Resource quota e limits (namespace ja criado pelo Terraform)
kubectl apply -f resource-quota.yaml

# 2. ServiceAccounts (cria identidades e RBAC)
kubectl apply -f serviceaccount-inference.yaml
kubectl apply -f serviceaccount-process.yaml

# 3. Workloads (inclui ConfigMaps, HPA, PDBs, TGB)
kubectl apply -f inference/
kubectl apply -f process/

# 4. KEDA ScaledObject
kubectl apply -f keda/
```

## Comandos Uteis

```bash
# Verificar namespace
kubectl get namespace fraud-detection

# Verificar quota
kubectl describe resourcequota fraud-detection-quota -n fraud-detection

# Verificar todos os recursos
kubectl get all -n fraud-detection

# Verificar serviceaccounts
kubectl get serviceaccounts -n fraud-detection

# Verificar pods
kubectl get pods -n fraud-detection

# Verificar logs de todos os pods
kubectl logs -n fraud-detection -l app=inference --tail=50
kubectl logs -n fraud-detection -l app=process --tail=50

# Verificar eventos
kubectl get events -n fraud-detection --sort-by='.lastTimestamp'

# Deletar todos os recursos (cuidado!)
kubectl delete -f inference/
kubectl delete -f process/
kubectl delete -f keda/
kubectl delete -f serviceaccount-inference.yaml
kubectl delete -f serviceaccount-process.yaml
kubectl delete -f namespace.yaml
```

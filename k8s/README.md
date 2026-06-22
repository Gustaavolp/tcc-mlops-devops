# Kubernetes Manifests

Manifests Kubernetes para os workloads do sistema de deteccao de fraude executados no cluster EKS.

---

## Estrutura de Diretorios

```
k8s/
├── dev/                                  # Ambiente de desenvolvimento (us-east-1)
│   ├── resource-quota.yaml               # ResourceQuota + LimitRange
│   ├── serviceaccount-inference.yaml     # ServiceAccount + RBAC (inference)
│   ├── serviceaccount-process.yaml       # ServiceAccount + RBAC (process)
│   ├── inference/
│   │   ├── deployment.yaml               # Deployment da API
│   │   ├── service.yaml                  # ClusterIP Service
│   │   ├── configmap.yaml                # ConfigMap (env vars)
│   │   ├── hpa.yaml                      # HorizontalPodAutoscaler
│   │   ├── pdb.yaml                      # PodDisruptionBudget
│   │   └── target-group-binding.yaml     # TargetGroupBinding (NLB)
│   ├── process/
│   │   ├── deployment.yaml               # Deployment do worker SQS
│   │   ├── configmap.yaml                # ConfigMap (env vars)
│   │   └── pdb.yaml                      # PodDisruptionBudget
│   └── keda/
│       └── process-scaledobject.yaml     # KEDA ScaledObject (SQS trigger)
│
└── staging/                              # Ambiente de staging (sa-east-1)
    └── (mesma estrutura)
```

---

## Workloads

O sistema possui dois workloads principais executando no namespace `fraud-detection`:

| Workload | Tipo | Funcao | Porta |
|----------|------|--------|-------|
| **inference** | API HTTP | Scoring de fraude em tempo real (SLA p95 < 500ms) | 8000 |
| **process** | Worker SQS | Processamento assincrono de feedback | - |

### Fluxo de Dados

```
SINCRONO (Scoring):
API Gateway → NLB → ALB → Service (inference) → Pod → DynamoDB/SageMaker

ASSINCRONO (Feedback):
SQS FIFO → Pod (process) → DynamoDB + Firehose → S3
```

---

## Configuracao por Ambiente

### Inference (API)

| Configuracao | DEV | STAGING |
|--------------|-----|---------|
| Regiao AWS | us-east-1 | sa-east-1 |
| Replicas iniciais | 2 | 2 |
| HPA min/max | 2-6 | 8-12 |
| Target CPU | 50% | 35% |
| Target Memory | 75% | 75% |
| CPU request/limit | 500m / 1000m | 500m / 1000m |
| Memory request/limit | 512Mi / 1Gi | 512Mi / 1Gi |

### Process (Worker)

| Configuracao | DEV | STAGING |
|--------------|-----|---------|
| Regiao AWS | us-east-1 | sa-east-1 |
| Replicas iniciais | 1 | 1 |
| KEDA min/max | 1-5 | 1-10 |
| Queue length (msgs/pod) | 30 | 50 |
| Scale-up rate | 1 pod/15s | 2 pods/15s |
| CPU request/limit | 100m / 500m | 100m / 500m |
| Memory request/limit | 256Mi / 512Mi | 256Mi / 512Mi |

---

## Namespace

O namespace `fraud-detection` inclui limites de recursos para proteger o cluster:

### ResourceQuota

Dimensionado por ambiente para suportar a escala configurada em HPA/KEDA:

| Recurso | DEV | STAGING |
|---------|-----|---------|
| CPU requests | 4 cores | 8 cores |
| CPU limits | 8 cores | 20 cores |
| Memory requests | 8 GiB | 12 GiB |
| Memory limits | 16 GiB | 24 GiB |
| Pods | 20 | 30 |
| Services | 10 | 10 |
| ConfigMaps | 20 | 20 |
| Secrets | 20 | 20 |
| PVCs | 5 | 5 |

### LimitRange (defaults)

Aplicado automaticamente a containers sem especificacao:

| Recurso | Request | Limit |
|---------|---------|-------|
| CPU | 100m | 500m |
| Memory | 128Mi | 512Mi |

---

## Auto-Scaling

### Inference (HPA)

Escala baseado em CPU e memoria:

| Comportamento | Configuracao |
|---------------|--------------|
| Scale-up | Imediato, +100%/min ou +2 pods/min (mais agressivo) |
| Scale-down | 5 min estabilizacao, -50%/min ou -1 pod/min (mais conservador) |

### Process (KEDA)

Escala baseado na profundidade da fila SQS:

| Comportamento | Configuracao |
|---------------|--------------|
| Polling interval | 15 segundos |
| Cooldown period | 60 segundos |
| Scale-up | Imediato |
| Scale-down | 2 min estabilizacao |

---

## Health Probes (Inference)

| Probe | Endpoint | Delay Inicial | Intervalo | Timeout | Falhas |
|-------|----------|---------------|-----------|---------|--------|
| Startup | /health | 30s | 10s | 5s | 18 (180s total) |
| Readiness | /health | 10s | 10s | 3s | 2 |
| Liveness | /health | 60s | 30s | 5s | 3 |

O worker `process` nao possui health probes HTTP pois nao expoe endpoints.

---

## Seguranca

### Pod Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

### ServiceAccounts

| ServiceAccount | Workload | Permissoes AWS (via Node IAM Role) |
|----------------|----------|-----------------------------------|
| inference-service | inference | DynamoDB, SageMaker, S3 (read) |
| process-service | process | SQS, DynamoDB, S3 (full), Firehose |

**Nota:** IRSA (IAM Roles for Service Accounts) nao esta disponivel devido a restricoes SCP. Os pods herdam permissoes do Node IAM Role do EKS.

### RBAC

Cada ServiceAccount possui Role e RoleBinding com permissoes minimas:

- ConfigMaps: get, list, watch
- Secrets: get, list
- Events: create, patch
- Leases (apenas process): get, list, watch, create, update, patch, delete

---

## Graceful Shutdown

| Workload | Termination Grace Period | PreStop Hook |
|----------|--------------------------|--------------|
| inference | 30s | sleep 5s |
| process | 60s | sleep 10s |

---

## Integracao com Terraform

O Terraform (stack `platform-k8s`) gerencia apenas os **add-ons de cluster** e o **namespace**:

| Recurso | Ferramenta |
|---------|-----------|
| Helm releases (Metrics Server, Cluster Autoscaler, AWS LB Controller, KEDA) | Terraform |
| Namespace `fraud-detection` | Terraform |
| ConfigMaps, HPA, PDBs, KEDA ScaledObjects, TargetGroupBindings | **kubectl (este diretorio)** |
| Deployments, Services, ServiceAccounts, RBAC | **kubectl (este diretorio)** |

Todos os arquivos YAML neste diretorio sao manifests **ativos** gerenciados via `kubectl apply`.

---

## Comandos

### Configurar kubeconfig

```bash
# DEV (us-east-1)
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1

# STAGING (sa-east-1)
aws eks update-kubeconfig --name elo-fraud-cluster-staging --region sa-east-1
```

### Aplicar Manifests

```bash
# Aplicar resource quota e service accounts (ordem importante)
kubectl apply -f k8s/{env}/resource-quota.yaml
kubectl apply -f k8s/{env}/serviceaccount-inference.yaml
kubectl apply -f k8s/{env}/serviceaccount-process.yaml

# Aplicar todos os manifests de workload
kubectl apply -f k8s/{env}/inference/
kubectl apply -f k8s/{env}/process/
kubectl apply -f k8s/{env}/keda/
```

### Verificar Status

```bash
# Pods
kubectl get pods -n fraud-detection

# HPA
kubectl get hpa -n fraud-detection

# KEDA ScaledObject
kubectl get scaledobject -n fraud-detection

# Logs
kubectl logs -f deployment/inference -n fraud-detection
kubectl logs -f deployment/process -n fraud-detection

# Metricas de recursos
kubectl top pods -n fraud-detection
```

### Escalar Manualmente

```bash
# Inference
kubectl scale deployment/inference --replicas=4 -n fraud-detection

# Process
kubectl scale deployment/process --replicas=2 -n fraud-detection
```

### Rollback

```bash
# Ver historico
kubectl rollout history deployment/inference -n fraud-detection

# Rollback para revisao anterior
kubectl rollout undo deployment/inference -n fraud-detection

# Rollback para revisao especifica
kubectl rollout undo deployment/inference --to-revision=2 -n fraud-detection
```

---

## Variaveis de Ambiente

### Inference

| Variavel | Descricao |
|----------|-----------|
| AWS_REGION | Regiao AWS |
| DYNAMO_TABLE | Tabela DynamoDB de historico |
| MLFLOW_TRACKING_URI | URI do MLflow Tracking Server |
| MODEL_NAME | Nome do modelo no registry |
| SQS_QUEUE_URL | URL da fila SQS para logs |

### Process

| Variavel | Descricao |
|----------|-----------|
| AWS_REGION | Regiao AWS |
| SQS_QUEUE_URL | URL da fila SQS FIFO |
| DYNAMO_TABLE | Tabela DynamoDB para updates |
| FIREHOSE_STREAM | Stream Firehose de transacoes |

---

## Pod Affinity

### Anti-Affinity

Pods do mesmo workload sao distribuidos entre nodes diferentes (HA):

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      topologyKey: kubernetes.io/hostname
```

### Node Affinity

Prefere nodes com label `role=general`:

```yaml
nodeAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 1
      matchExpressions:
        - key: role
          operator: In
          values: [general]
```

---

---

## Troubleshooting

### Pod em CrashLoopBackOff

```bash
# Ver eventos do pod
kubectl describe pod <pod-name> -n fraud-detection

# Ver logs do container anterior
kubectl logs <pod-name> -n fraud-detection --previous
```

### Pod nao recebe trafego

```bash
# Verificar se readiness probe esta passando
kubectl get pods -n fraud-detection -o wide

# Verificar endpoints do service
kubectl get endpoints inference -n fraud-detection

# Verificar TargetGroupBinding
kubectl describe targetgroupbinding -n fraud-detection
```

### HPA nao escala

```bash
# Verificar metricas
kubectl get hpa inference-hpa -n fraud-detection -o yaml

# Verificar metrics-server
kubectl top pods -n fraud-detection
```

### KEDA nao escala

```bash
# Verificar ScaledObject
kubectl describe scaledobject process-scaledobject -n fraud-detection

# Verificar logs do KEDA operator
kubectl logs -n keda -l app=keda-operator
```

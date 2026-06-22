# Cluster Kubernetes (EKS) - ELO Fraud Detection

**Cluster:** elo-fraud-cluster-dev
**Versão:** Kubernetes 1.32
**Região:** us-east-1
**Namespace:** fraud-detection
**Data:** 2025-11-23

---

## Arquitetura do Cluster EKS

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ EKS CLUSTER: elo-fraud-cluster-dev                                                            │
│ Version: 1.32 │ Region: us-east-1 │ IRSA: ✅ Enabled                                          │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ EKS CONTROL PLANE (AWS Managed)                                                               │
│                                                                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                              │
│  │ API Server      │  │ etcd            │  │ Scheduler       │                              │
│  │ (HA - 3 AZs)    │  │ (HA - 3 AZs)    │  │ (HA - 3 AZs)    │                              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                              │
│                                                                                                │
│  Logging → CloudWatch: api, audit                                                             │
│  Endpoint Access: Public ✅ + Private ✅                                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ ADDONS (AWS Managed Add-ons)                                                                  │
│                                                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐             │
│  │ coredns      │  │ kube-proxy   │  │ vpc-cni      │  │ aws-ebs-csi-driver   │             │
│  │ (DNS)        │  │ (Networking) │  │ (AWS CNI)    │  │ (commented)          │             │
│  │ Most Recent  │  │ Most Recent  │  │ Most Recent  │  │ Manual setup needed  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────────┘             │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ NAMESPACE: fraud-detection                                                                     │
│ Labels: environment=dev, project=elo-fraud-detection, managed-by=terraform                   │
│                                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ DEPLOYMENT: inference                                                                    │ │
│  │                                                                                          │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ ReplicaSet (managed by Deployment)                                                 │ │ │
│  │  │ Replicas: 1-4 (managed by HPA)                                                     │ │ │
│  │  │ Strategy: RollingUpdate (maxSurge: 1, maxUnavailable: 0)                          │ │ │
│  │  │                                                                                     │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────────────┐  │ │ │
│  │  │  │ POD: inference-xxxx-yyyy                                                     │  │ │ │
│  │  │  │ Labels: app=inference, component=api, version=v1                            │  │ │ │
│  │  │  │ ServiceAccount: inference-sa (IRSA)                                         │  │ │ │
│  │  │  │                                                                              │  │ │ │
│  │  │  │  ┌────────────────────────────────────────────────────────────────────────┐ │  │ │ │
│  │  │  │  │ CONTAINER: inference                                                   │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Image: 888577064416.dkr.ecr.us-east-1.amazonaws.com/               │ │  │ │ │
│  │  │  │  │        elo-fraud-inference-dev:latest                                  │ │  │ │ │
│  │  │  │  │ Pull Policy: Always                                                    │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Ports:                                                                 │ │  │ │ │
│  │  │  │  │   - containerPort: 8000 (HTTP API)                                    │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Resources:                                                             │ │  │ │ │
│  │  │  │  │   Requests: CPU 500m, Memory 2Gi                                      │ │  │ │ │
│  │  │  │  │   Limits:   CPU 1000m, Memory 2.5Gi                                   │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Environment Variables:                                                 │ │  │ │ │
│  │  │  │  │   ENV: dev                                                             │ │  │ │ │
│  │  │  │  │   AWS_REGION: us-east-1                                               │ │  │ │ │
│  │  │  │  │   DDB_TABLE_NAME: elo-fraud-customer-recent-tx-dev                   │ │  │ │ │
│  │  │  │  │   SAGEMAKER_ENDPOINT_NAME: elo-fraud-fraud-score-dev                 │ │  │ │ │
│  │  │  │  │   SQS_QUEUE_URL: https://sqs.../fraud-detection-results-dev.fifo     │ │  │ │ │
│  │  │  │  │   LOG_LEVEL: INFO                                                      │ │  │ │ │
│  │  │  │  │   LOG_FORMAT: json                                                     │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Probes:                                                                │ │  │ │ │
│  │  │  │  │   Startup:   GET /health (timeout 3s, failures 12)                    │ │  │ │ │
│  │  │  │  │   Readiness: GET /health (period 10s, failures 2)                     │ │  │ │ │
│  │  │  │  │   Liveness:  GET /health (period 30s, failures 3)                     │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Security:                                                              │ │  │ │ │
│  │  │  │  │   runAsNonRoot: true                                                   │ │  │ │ │
│  │  │  │  │   runAsUser: 1000                                                      │ │  │ │ │
│  │  │  │  │   fsGroup: 1000                                                        │ │  │ │ │
│  │  │  │  └─────────────────────────────────────────────────────────────────────┘ │  │ │ │
│  │  │  │                                                                              │  │ │ │
│  │  │  │  Affinity:                                                                   │  │ │ │
│  │  │  │    podAntiAffinity: Prefer different nodes (spread across AZs)             │  │ │ │
│  │  │  │    nodeAffinity: Prefer nodes with role=general                             │  │ │ │
│  │  │  │                                                                              │  │ │ │
│  │  │  │  Annotations:                                                                │  │ │ │
│  │  │  │    prometheus.io/scrape: "true"                                             │  │ │ │
│  │  │  │    prometheus.io/port: "8000"                                               │  │ │ │
│  │  │  │    prometheus.io/path: "/metrics"                                           │  │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────────────┘  │ │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ SERVICE: inference                                                                       │ │
│  │ Type: ClusterIP                                                                          │ │
│  │ Selector: app=inference                                                                  │ │
│  │                                                                                          │ │
│  │  Ports:                                                                                  │ │
│  │    - name: http                                                                          │ │
│  │      port: 8000                                                                          │ │
│  │      targetPort: 8000                                                                    │ │
│  │      protocol: TCP                                                                       │ │
│  │                                                                                          │ │
│  │  ClusterIP: 10.100.x.x (auto-assigned)                                                  │ │
│  │  Session Affinity: None                                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ INGRESS: inference-ingress                                                               │ │
│  │ IngressClass: alb (AWS Load Balancer Controller)                                        │ │
│  │                                                                                          │ │
│  │  Annotations:                                                                            │ │
│  │    alb.ingress.kubernetes.io/scheme: internal                                           │ │
│  │    alb.ingress.kubernetes.io/target-type: ip                                            │ │
│  │    alb.ingress.kubernetes.io/load-balancer-name: elo-fraud-alb-eks-dev                 │ │
│  │    alb.ingress.kubernetes.io/healthcheck-path: /health                                  │ │
│  │    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'                            │ │
│  │                                                                                          │ │
│  │  Rules:                                                                                  │ │
│  │    - http:                                                                               │ │
│  │        paths:                                                                            │ │
│  │          - path: /                                                                       │ │
│  │            pathType: Prefix                                                              │ │
│  │            backend:                                                                      │ │
│  │              service: inference                                                          │ │
│  │              port: 8000                                                                  │ │
│  │                                                                                          │ │
│  │  ⚡ Creates AWS ALB:                                                                     │ │
│  │     Name: elo-fraud-alb-eks-dev                                                         │ │
│  │     Scheme: internal (VPC only)                                                          │ │
│  │     Target Group: IP mode (direct to pod IPs)                                           │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ HPA: inference-hpa (HorizontalPodAutoscaler)                                            │ │
│  │ Target: Deployment/inference                                                             │ │
│  │                                                                                          │ │
│  │  Replicas:                                                                               │ │
│  │    Min: 1                                                                                │ │
│  │    Max: 4                                                                                │ │
│  │                                                                                          │ │
│  │  Metrics:                                                                                │ │
│  │    - Type: Resource                                                                      │ │
│  │      Resource: cpu                                                                       │ │
│  │      Target: 70% utilization                                                             │ │
│  │                                                                                          │ │
│  │  Behavior:                                                                               │ │
│  │    Scale UP:   100% or 2 pods per minute (Max policy)                                  │ │
│  │    Scale DOWN: 50% or 1 pod per minute (Min policy) + 5min stabilization              │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ DEPLOYMENT: process                                                                      │ │
│  │                                                                                          │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ ReplicaSet (managed by Deployment)                                                 │ │ │
│  │  │ Replicas: 1 (static, no HPA)                                                       │ │ │
│  │  │ Strategy: RollingUpdate (maxSurge: 1, maxUnavailable: 0)                          │ │ │
│  │  │                                                                                     │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────────────┐  │ │ │
│  │  │  │ POD: process-xxxx-yyyy                                                       │  │ │ │
│  │  │  │ Labels: app=process, component=worker, version=v1                           │  │ │ │
│  │  │  │ ServiceAccount: process-sa (IRSA)                                           │  │ │ │
│  │  │  │                                                                              │  │ │ │
│  │  │  │  ┌────────────────────────────────────────────────────────────────────────┐ │  │ │ │
│  │  │  │  │ CONTAINER: process                                                     │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Image: 888577064416.dkr.ecr.us-east-1.amazonaws.com/               │ │  │ │ │
│  │  │  │  │        elo-fraud-process-dev:latest                                    │ │  │ │ │
│  │  │  │  │ Pull Policy: Always                                                    │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Ports: None (background worker)                                        │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Resources:                                                             │ │  │ │ │
│  │  │  │  │   Requests: CPU 250m, Memory 1Gi                                      │ │  │ │ │
│  │  │  │  │   Limits:   CPU 500m, Memory 1.5Gi                                    │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Environment Variables:                                                 │ │  │ │ │
│  │  │  │  │   ENV: dev                                                             │ │  │ │ │
│  │  │  │  │   AWS_REGION: us-east-1                                               │ │  │ │ │
│  │  │  │  │   SQS_QUEUE_URL: https://sqs.../elo-fraud-transactions-dev.fifo      │ │  │ │ │
│  │  │  │  │   BATCH_SIZE: 10                                                       │ │  │ │ │
│  │  │  │  │   WAIT_TIME_SECONDS: 20                                               │ │  │ │ │
│  │  │  │  │   VISIBILITY_TIMEOUT: 300                                              │ │  │ │ │
│  │  │  │  │   DDB_TABLE_NAME: elo-fraud-customer-recent-tx-dev                   │ │  │ │ │
│  │  │  │  │   S3_BUCKET_PROCESSED: elo-fraud-data-processed-dev                  │ │  │ │ │
│  │  │  │  │   LOG_LEVEL: INFO                                                      │ │  │ │ │
│  │  │  │  │   LOG_FORMAT: json                                                     │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Probes: None (background job, no HTTP endpoint)                       │ │  │ │ │
│  │  │  │  │                                                                         │ │  │ │ │
│  │  │  │  │ Security:                                                              │ │  │ │ │
│  │  │  │  │   runAsNonRoot: true                                                   │ │  │ │ │
│  │  │  │  │   runAsUser: 1000                                                      │ │  │ │ │
│  │  │  │  │   fsGroup: 1000                                                        │ │  │ │ │
│  │  │  │  └─────────────────────────────────────────────────────────────────────┘ │  │ │ │
│  │  │  │                                                                              │  │ │ │
│  │  │  │  Termination Grace Period: 60s (longer than inference)                     │  │ │ │
│  │  │  │  preStop Hook: sleep 10                                                     │  │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────────────┘  │ │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                │
│  No Service for process (background worker, no network exposure needed)                      │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ NODE GROUP: general                                                                            │
│                                                                                                │
│  ┌──────────────────────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │ EC2 Node 1                               │  │ EC2 Node 2 (scales as needed)            │  │
│  │ AZ: us-east-1a                           │  │ AZ: us-east-1b                           │  │
│  │ Type: t3.medium                          │  │ Type: t3.medium                          │  │
│  │ AMI: AL2023_x86_64_STANDARD              │  │ AMI: AL2023_x86_64_STANDARD              │  │
│  │                                          │  │                                          │  │
│  │ Labels:                                  │  │ Labels:                                  │  │
│  │   role: general                          │  │   role: general                          │  │
│  │                                          │  │                                          │  │
│  │ Capacity:                                │  │ EBS Volume:                              │  │
│  │   vCPU: 2                                │  │   Type: gp3                              │  │
│  │   Memory: 4 GiB                          │  │   Size: 50 GB                            │  │
│  │                                          │  │   IOPS: 3000                             │  │
│  │ Running Pods:                            │  │   Throughput: 125 MB/s                   │  │
│  │   - inference-xxxx (1 pod)              │  │   Encrypted: Yes                         │  │
│  │   - process-xxxx (1 pod)                │  │                                          │  │
│  │   - coredns (system)                     │  │ Auto Scaling: ✅                         │  │
│  │   - kube-proxy (system)                  │  │   Min: 1                                 │  │
│  │   - aws-node (vpc-cni)                   │  │   Max: 3                                 │  │
│  └──────────────────────────────────────────┘  │   Desired: 1                             │  │
│                                                 └──────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Resumo de Workloads

| Workload | Tipo | Replicas | CPU | Memória | HPA |
|----------|------|----------|-----|---------|-----|
| inference | Deployment | 1-4 | 500m-1000m | 2-2.5Gi | ✅ |
| process | Deployment | 1 | 250m-500m | 1-1.5Gi | ❌ |

## Services e Ingress

| Nome | Tipo | Porta | Target |
|------|------|-------|--------|
| inference | ClusterIP | 8000 | Pods inference:8000 |
| inference-ingress | ALB (internal) | 80 | Service inference:8000 |

## Autoscaling

- **HPA Inference:** CPU > 70% → scale 1-4 replicas
- **Cluster Autoscaler:** Node group 1-3 nodes (t3.medium)

## Segurança

- **ServiceAccounts:** inference-sa, process-sa (IRSA pending)
- **Security Context:** runAsNonRoot, UID 1000
- **Network Policies:** Não configuradas (TODO)

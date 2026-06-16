# Resumo Executivo - ELO Fraud Detection

**Projeto:** ELO Fraud Detection
**Ambiente:** Desenvolvimento (dev)
**AWS Account:** 888577064416
**Região:** us-east-1
**Data da Análise:** 2025-11-23

---

## Visão Geral

Este documento apresenta um resumo executivo da arquitetura do projeto ELO Fraud Detection, incluindo custos, pontos de atenção e próximos passos recomendados.

---

## Custos Mensais Estimados (Desenvolvimento)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ CUSTO TOTAL MENSAL ESTIMADO: $210-280 USD                                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ COMPUTE:                                                                                │
│   EKS Control Plane              $0          (Free in AWS)                             │
│   EKS Node Group (t3.medium)     $30-45      (1 node x $0.0416/h x 730h)              │
│   SageMaker Endpoint             $100-120    (ml.m6g.large x $0.154/h x 730h)         │
│   Total Compute:                 $130-165                                              │
│                                                                                         │
│ NETWORKING:                                                                             │
│   ALB                            $18         ($16 base + $0.006/LCU)                   │
│   VPC Endpoints (Interface 4x)   $29         ($7.20/month each)                        │
│   VPC Endpoints (Gateway 2x)     $0          (S3, DynamoDB - free)                     │
│   Total Networking:              $47                                                    │
│                                                                                         │
│ STORAGE:                                                                                │
│   S3 (4 buckets)                 $2-5        (depends on data volume)                  │
│   DynamoDB                       $0-2        (PAY_PER_REQUEST, low traffic)            │
│   ECR (3 repos)                  $0-1        (depends on image size)                   │
│   Total Storage:                 $2-8                                                  │
│                                                                                         │
│ ML & ANALYTICS:                                                                         │
│   MLflow Server (Small)          $38         (2 vCPU, 4GB RAM)                         │
│   SageMaker Studio Domain        $0          (charged per user session)                │
│   Total ML:                      $38                                                    │
│                                                                                         │
│ MESSAGING:                                                                              │
│   SQS FIFO (2 queues)            $0-1        (depends on volume)                       │
│   CloudWatch Logs                $1-3        (depends on log volume)                   │
│   Total Messaging:               $1-4                                                  │
│                                                                                         │
│ API GATEWAY:                                                                            │
│   REST API                       $0-3        (first 1M requests free)                  │
│   Total API:                     $0-3                                                  │
│                                                                                         │
│ ═══════════════════════════════════════════════════════════════════════════════════════ │
│ TOTAL MONTHLY (DEV):             $218-283 USD                                          │
│                                                                                         │
│ OPTIMIZATIONS APPLIED:                                                                  │
│   ✅ NAT Gateway removed → VPC Endpoints ($32/mo → $29/mo)                             │
│   ✅ EKS nodes reduced (2 → 1) (~$30/mo savings)                                       │
│   ✅ Inference replicas reduced (2 → 1) (~$15/mo savings)                              │
│   ✅ No HTTPS/WAF in dev (~$20/mo savings)                                             │
│   ✅ DynamoDB on-demand pricing (~$10/mo savings vs provisioned)                       │
│                                                                                         │
│ TOTAL SAVINGS VS ORIGINAL: ~$107/month                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Projeção de Custos para Produção

| Item | Dev | Prod (Estimado) | Delta |
|------|-----|-----------------|-------|
| EKS Nodes | $30-45 | $150-200 | +$120 |
| SageMaker Endpoint | $100-120 | $300-400 | +$240 |
| NAT Gateway | $0 | $64 | +$64 |
| ALB | $18 | $30 | +$12 |
| VPC Endpoints | $29 | $29 | $0 |
| WAF | $0 | $20 | +$20 |
| Certificate Manager | $0 | $0 | $0 |
| CloudWatch/Logs | $1-3 | $20-40 | +$30 |
| **TOTAL** | **$218-283** | **$713-903** | **+$486** |

**Observação:** Produção requer multi-AZ, NAT Gateway, mais replicas, e maior capacidade.

---

## Pontos de Atenção e Recomendações

### 1. Segurança

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. SEGURANÇA                                                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ❌ CRÍTICO - Network Policies não configuradas                                         │
│    → Recomendação: Implementar NetworkPolicy no Kubernetes                             │
│    → Permitir apenas tráfego necessário entre pods                                     │
│                                                                                         │
│ ❌ CRÍTICO - IRSA não habilitada para pods EKS                                         │
│    → Recomendação: Descomentar roles eks_inference e eks_process em IAM               │
│    → Adicionar anotações nos ServiceAccounts para assumir roles                        │
│                                                                                         │
│ ⚠️  ATENÇÃO - ALB sem HTTPS em dev                                                     │
│    → Recomendação: Adicionar ACM certificate e listener HTTPS:443 para prod           │
│                                                                                         │
│ ⚠️  ATENÇÃO - Buckets S3 sem bucket policies                                          │
│    → Limitação: SCP organizacional bloqueia s3:PutBucketPolicy                        │
│    → Workaround: Usar IAM policies em roles (já implementado)                          │
│                                                                                         │
│ ✅ BOM - Security Context configurado (runAsNonRoot, UID 1000)                         │
│ ✅ BOM - VPC Endpoints para comunicação privada com AWS services                       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Observabilidade

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. OBSERVABILIDADE                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ❌ CRÍTICO - Logging centralizado desativado                                           │
│    → Fluent Bit DaemonSet foi removido                                                 │
│    → Recomendação: Reinstalar Fluent Bit ou usar AWS for Fluent Bit                   │
│    → Alternativa: Configurar CloudWatch Container Insights                             │
│                                                                                         │
│ ⚠️  ATENÇÃO - Prometheus não instalado                                                │
│    → Anotações prometheus.io/* já configuradas nos pods                                │
│    → Recomendação: Instalar kube-prometheus-stack via Helm                             │
│    → Metrics endpoint: /metrics já exposto em ambos serviços                           │
│                                                                                         │
│ ⚠️  ATENÇÃO - Sem dashboards ou alerting                                              │
│    → Recomendação: Configurar Grafana + AlertManager                                   │
│    → CloudWatch Alarms criados mas sem SNS topic                                       │
│                                                                                         │
│ ✅ BOM - LOG_LEVEL e LOG_FORMAT configurados (INFO, json)                              │
│ ✅ BOM - CloudWatch Logs habilitado para EKS control plane                             │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Alta Disponibilidade

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. ALTA DISPONIBILIDADE                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ✅ BOM - Multi-AZ deployment (us-east-1a, us-east-1b)                                  │
│ ✅ BOM - ALB cross-zone balancing habilitado                                           │
│ ✅ BOM - HPA configurado para inference (1-4 replicas)                                 │
│ ✅ BOM - Pod anti-affinity (spread across nodes)                                       │
│ ✅ BOM - RollingUpdate com 0 unavailable (zero downtime)                               │
│                                                                                         │
│ ⚠️  ATENÇÃO - Process worker sem HA (1 replica fixa)                                  │
│    → Recomendação: Implementar HPA baseado em SQS queue depth                          │
│    → Métrica: ApproximateNumberOfMessagesVisible                                       │
│                                                                                         │
│ ⚠️  ATENÇÃO - SageMaker endpoint single instance                                      │
│    → Recomendação: Aumentar instance_count para 2+ em produção                         │
│                                                                                         │
│ ❌ CRÍTICO - Sem disaster recovery definido                                            │
│    → Recomendação: Definir RTO/RPO                                                     │
│    → Implementar backups automáticos (DynamoDB, S3 versioning)                         │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Performance

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. PERFORMANCE                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ✅ BOM - SageMaker endpoint ARM64 (ml.m6g.large - 20% cheaper)                         │
│ ✅ BOM - SQS long polling (20s - reduz API calls)                                      │
│ ✅ BOM - DynamoDB PAY_PER_REQUEST (sem throttling)                                     │
│ ✅ BOM - API Gateway throttling configurado (10k RPS)                                  │
│ ✅ BOM - ALB connection draining (30s)                                                 │
│                                                                                         │
│ ⚠️  ATENÇÃO - EKS nodes t3.medium (burstable)                                         │
│    → Recomendação: Monitorar CPU credits                                               │
│    → Considerar c6i/c6a para workloads CPU-intensive em prod                           │
│                                                                                         │
│ ⚠️  ATENÇÃO - Sem cache configurado                                                   │
│    → Recomendação: Considerar ElastiCache Redis para hot data                          │
│    → Reduzir latência de DynamoDB reads                                                │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Próximos Passos Recomendados

### FASE 1: Deployment Inicial (Sprint 1)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: DEPLOYMENT INICIAL (Sprint 1)                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ 1. Validar e aplicar Terraform                                                         │
│    □ terraform fmt -recursive                                                          │
│    □ terraform validate                                                                 │
│    □ terraform plan -out=tfplan                                                         │
│    □ Revisar plano com time                                                            │
│    □ terraform apply tfplan                                                             │
│                                                                                         │
│ 2. Configurar acesso ao cluster EKS                                                    │
│    □ aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1        │
│    □ kubectl get nodes                                                                  │
│    □ kubectl get namespaces                                                             │
│                                                                                         │
│ 3. Instalar AWS Load Balancer Controller                                               │
│    □ helm repo add eks https://aws.github.io/eks-charts                                │
│    □ helm install aws-load-balancer-controller eks/aws-load-balancer-controller \     │
│         --set clusterName=elo-fraud-cluster-dev \                                      │
│         --set serviceAccount.create=false \                                             │
│         --set serviceAccount.name=aws-load-balancer-controller                         │
│                                                                                         │
│ 4. Deploy Kubernetes manifests                                                         │
│    □ kubectl apply -f k8s/dev/namespace.yaml                                           │
│    □ kubectl apply -f k8s/dev/inference/                                               │
│    □ kubectl apply -f k8s/dev/process/                                                 │
│    □ kubectl get pods -n fraud-detection --watch                                       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### FASE 2: Configuração de Segurança (Sprint 2)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: CONFIGURAÇÃO DE SEGURANÇA (Sprint 2)                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ 5. Configurar IRSA para pods EKS                                                       │
│    □ Descomentar roles em infra/modules/iam/main.tf                                   │
│    □ terraform apply                                                                    │
│    □ Anotar ServiceAccounts com role ARN                                               │
│    □ Testar acesso a DynamoDB/SQS/S3 dos pods                                          │
│                                                                                         │
│ 6. Implementar Network Policies                                                        │
│    □ Criar NetworkPolicy para deny-all ingress                                         │
│    □ Criar NetworkPolicy allow inference → sagemaker                                   │
│    □ Criar NetworkPolicy allow process → sqs/dynamodb                                  │
│    □ Testar conectividade                                                              │
│                                                                                         │
│ 7. Criar SNS topic para alarmes                                                        │
│    □ aws sns create-topic --name elo-fraud-alarms-dev                                  │
│    □ aws sns subscribe --topic-arn <arn> --protocol email --notification-endpoint ... │
│    □ Atualizar CloudWatch alarms com actions                                           │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### FASE 3: Observabilidade (Sprint 3)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: OBSERVABILIDADE (Sprint 3)                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ 8. Instalar stack de monitoramento                                                     │
│    □ helm repo add prometheus-community \                                              │
│        https://prometheus-community.github.io/helm-charts                              │
│    □ helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack    │
│    □ kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80                    │
│    □ Importar dashboards (Kubernetes cluster, pods, SQS, DynamoDB)                     │
│                                                                                         │
│ 9. Reinstalar logging centralizado                                                     │
│    □ Opção 1: AWS for Fluent Bit DaemonSet                                            │
│    □ Opção 2: CloudWatch Container Insights                                            │
│    □ Configurar log retention policies                                                 │
│    □ Criar log insights queries                                                        │
│                                                                                         │
│ 10. Configurar tracing distribuído (opcional)                                         │
│     □ AWS X-Ray ou OpenTelemetry                                                       │
│     □ Instrumentar aplicações                                                          │
│     □ Criar service map                                                                │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### FASE 4: ML Pipeline (Sprint 4)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: ML PIPELINE (Sprint 4)                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ 11. Deploy modelo no SageMaker                                                         │
│     □ Treinar modelo inicial (ou usar modelo dummy)                                    │
│     □ Upload para S3 models bucket                                                     │
│     □ Build Docker image do modelo                                                     │
│     □ Push para ECR elo-fraud-model-dev                                                │
│     □ Update SageMaker endpoint                                                        │
│                                                                                         │
│ 12. Configurar MLflow tracking                                                         │
│     □ Obter MLflow tracking URI                                                        │
│     □ Configurar notebooks SageMaker Studio                                            │
│     □ Criar experimento inicial                                                        │
│     □ Log metrics, parameters, artifacts                                               │
│                                                                                         │
│ 13. Testar pipeline end-to-end                                                         │
│     □ POST /v1/score com payload de teste                                              │
│     □ Verificar logs inference pod                                                     │
│     □ Confirmar mensagem em SQS                                                        │
│     □ Verificar process pod consumiu mensagem                                          │
│     □ Validar dados em DynamoDB                                                        │
│     □ Confirmar arquivo em S3 processed                                                │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Métricas de Sucesso

| Métrica | Target | Medição |
|---------|--------|---------|
| API Latency (p95) | < 300ms | CloudWatch metrics |
| Inference Latency (p95) | < 200ms | SageMaker metrics |
| Queue Depth | < 1000 msgs | CloudWatch metrics |
| Error Rate | < 1% | Application logs |
| Uptime (SLA) | > 99% | CloudWatch uptime |
| Cost per transaction | < $0.01 | Custom metric |

---

## Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| SageMaker endpoint down | Alto | Baixa | Multi-instance deployment em prod |
| EKS node failure | Médio | Média | Node auto-scaling (1-3 nodes) |
| DynamoDB throttling | Médio | Baixa | PAY_PER_REQUEST mode |
| SQS message loss | Alto | Baixa | DLQ configurado, 14 dias retention |
| S3 data loss | Alto | Muito Baixa | Versioning habilitado |
| VPC endpoint outage | Médio | Muito Baixa | Multi-AZ deployment |

---

## Contatos

**DevOps Lead:** [Seu Nome]
**Cloud Architect:** [Nome]
**Data Science Lead:** [Nome]

**Última atualização:** 2025-11-23

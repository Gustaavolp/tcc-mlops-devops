# Platform-K8s Stack - DEV

## Visao Geral

A **Platform-K8s Stack** gerencia os **add-ons de cluster** (Helm releases) e o **namespace** para o EKS. Seguindo as melhores praticas da industria (HashiCorp, AWS EKS Blueprints, CNCF), esta stack gerencia apenas recursos de infraestrutura de cluster, enquanto os recursos de workload (ConfigMaps, HPA, PDBs, KEDA ScaledObjects, TargetGroupBindings) sao gerenciados via `kubectl` no diretorio `k8s/`.

### Separacao de Responsabilidades

| Camada | Ferramenta | Recursos |
|--------|-----------|----------|
| **Infraestrutura AWS** | Terraform (stacks foundation, platform) | VPC, EKS, DynamoDB, SQS, NLB |
| **Cluster Add-ons** | Terraform Helm (esta stack) | Metrics Server, Cluster Autoscaler, AWS LB Controller, KEDA, Namespace |
| **Workloads** | kubectl (diretorio `k8s/`) | Deployments, Services, ConfigMaps, HPA, PDBs, KEDA ScaledObjects, TargetGroupBindings |

### Por que uma Stack Separada?

| Beneficio | Descricao |
|-----------|-----------|
| **Providers Distintos** | Requer providers kubernetes, helm e kubectl alem do AWS |
| **Ciclo de Vida** | Add-ons mudam raramente, workloads mudam com frequencia |
| **Chicken-and-Egg** | Providers K8s precisam do endpoint do EKS no plan time |

---

## Recursos Provisionados

### Helm Releases

| Chart | Version | Namespace | Replicas | Funcao |
|-------|---------|-----------|----------|--------|
| **metrics-server** | 3.13.0 | kube-system | 1 | Metricas CPU/Memory para HPA |
| **cluster-autoscaler** | 9.55.0 | kube-system | 1 | Auto-scaling de nodes |
| **aws-load-balancer-controller** | 3.0.0 | kube-system | 2 | TargetGroupBinding CRDs |
| **keda** | 2.18.3 | keda | 1 | Event-driven autoscaling |

> **Nota:** IRSA esta desabilitado devido a SCP. Todos os add-ons usam IAM role do node.

### Namespace

| Atributo | Valor |
|----------|-------|
| **Nome** | fraud-detection |
| **Labels** | environment=dev, managed-by=terraform |

---

## Estrutura de Arquivos

```
infra/environments/dev/platform-k8s/
├── backend.tf     # Backend S3 para state
├── providers.tf   # Providers AWS, Kubernetes, Helm, Kubectl
├── data.tf        # Remote state da stack Platform
├── variables.tf   # Variaveis do projeto
├── addons.tf      # Helm releases (Metrics, Autoscaler, LB Controller) + Namespace
├── keda.tf        # KEDA Helm release
├── outputs.tf     # Outputs (status dos Helm releases)
└── README.md      # Esta documentacao
```

---

## Outputs

| Output | Descricao |
|--------|-----------|
| `metrics_server_status` | Status do Metrics Server |
| `cluster_autoscaler_status` | Status do Cluster Autoscaler |
| `aws_load_balancer_controller_status` | Status do AWS LB Controller |
| `keda_status` | Status do KEDA |
| `fraud_detection_namespace` | Nome do namespace |

---

## Dependencias

```
Platform ────────────────> Platform-K8s
    |
    ├── eks_cluster_name
    ├── eks_cluster_endpoint
    ├── eks_cluster_certificate_authority_data
    └── vpc_id
```

### Ordem de Implantacao

```
1. foundation
       |
       v
2. platform
       |
       v
3. platform-k8s  <-- ESTA STACK
       |
       v
4. kubectl apply -f k8s/dev/  (workloads)
```

---

## Guia de Implantacao

```bash
# 1. Configurar kubectl
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1

# 2. Inicializar e aplicar
cd infra/environments/dev/platform-k8s
terraform init
terraform plan
terraform apply

# 3. Verificar Helm releases
helm list -A
kubectl get pods -n kube-system
kubectl get pods -n keda

# 4. Aplicar workloads (diretorio k8s/)
kubectl apply -f k8s/dev/resource-quota.yaml
kubectl apply -f k8s/dev/serviceaccount-inference.yaml
kubectl apply -f k8s/dev/serviceaccount-process.yaml
kubectl apply -f k8s/dev/inference/
kubectl apply -f k8s/dev/process/
kubectl apply -f k8s/dev/keda/
```

---

## Operacoes

### Verificar Add-ons

```bash
# Helm releases
helm list -A

# Pods dos add-ons
kubectl get pods -n kube-system
kubectl get pods -n keda

# Metricas
kubectl top nodes
kubectl top pods -n fraud-detection
```

### Upgrade de Helm Charts

```bash
# Atualizar versao no addons.tf ou keda.tf
terraform plan
terraform apply
```

---

## Troubleshooting

### Provider kubernetes nao conecta

```bash
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1
kubectl cluster-info
```

### Metrics Server nao funciona

```bash
kubectl get deployment metrics-server -n kube-system
kubectl logs -l app.kubernetes.io/name=metrics-server -n kube-system
```

### CRD TargetGroupBinding nao encontrado

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
kubectl get crd | grep elbv2
```

### KEDA operator com erro

```bash
kubectl get deployment -n keda
kubectl logs -l app=keda-operator -n keda
```

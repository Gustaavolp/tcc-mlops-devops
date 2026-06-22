# EKS Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Node Group](#node-group)
- [Addons](#addons)
- [Seguranca](#seguranca)
- [Restricoes SCP](#restricoes-scp)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)
- [Custos Estimados](#custos-estimados)

---

## Visao Geral

Este modulo provisiona um cluster **Amazon EKS (Elastic Kubernetes Service)** para execucao dos servicos de deteccao de fraude.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Orquestracao** | Gerencia containers dos servicos inference e process |
| **Auto-scaling** | Escala nodes automaticamente baseado na demanda |
| **Alta Disponibilidade** | Nodes distribuidos em multiplas AZs |
| **Integracao AWS** | Acesso nativo a servicos AWS via IAM |

### Caracteristicas

| Caracteristica | Valor |
|----------------|-------|
| **Modulo Base** | terraform-aws-modules/eks/aws ~> 20.0 |
| **Cluster Version** | 1.32 (configuravel) |
| **Node Groups** | 1 managed node group multi-purpose |
| **AMI** | Amazon Linux 2023 x86_64 |
| **Capacity Type** | ON_DEMAND (latencia previsivel) |
| **Endpoint Access** | Publico + Privado |

---

## Arquitetura

```
                                    AWS Region: sa-east-1
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              EKS Control Plane                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                          │  │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │  │
│   │   │  API Server │   │    etcd     │   │ Controllers │                   │  │
│   │   │  (managed)  │   │  (managed)  │   │  (managed)  │                   │  │
│   │   └─────────────┘   └─────────────┘   └─────────────┘                   │  │
│   │                                                                          │  │
│   │   Endpoint: https://{cluster-id}.{region}.eks.amazonaws.com             │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                        │
│                                        │ API                                    │
│                                        ▼                                        │
│                              VPC (Private Subnets)                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                          │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │  │
│   │   │                   Managed Node Group: general                    │   │  │
│   │   │                                                                  │   │  │
│   │   │   AZ-a                    AZ-b                                 │   │  │
│   │   │   ┌──────────┐           ┌──────────┐                          │   │  │
│   │   │   │  Node 1  │           │  Node 2  │     (default: 2 nodes)   │   │  │
│   │   │   │          │           │          │                          │   │  │
│   │   │   │ ┌──────┐ │           │ ┌──────┐ │                          │   │  │
│   │   │   │ │ Pod  │ │           │ │ Pod  │ │                          │   │  │
│   │   │   │ │infer.│ │           │ │infer.│ │                          │   │  │
│   │   │   │ └──────┘ │           │ └──────┘ │                          │   │  │
│   │   │   │ ┌──────┐ │           │ ┌──────┐ │                          │   │  │
│   │   │   │ │ Pod  │ │           │ │ Pod  │ │                          │   │  │
│   │   │   │ │proc. │ │           │ │proc. │ │                          │   │  │
│   │   │   │ └──────┘ │           │ └──────┘ │                          │   │  │
│   │   │   └──────────┘           └──────────┘                          │   │  │
│   │   │                                                                  │   │  │
│   │   │   Instance: t3.medium (2 vCPU, 4GB) | Disk: 50GB gp3          │   │  │
│   │   │   Min: 2 | Max: 4 | Desired: 2                                  │   │  │
│   │   │                                                                  │   │  │
│   │   └─────────────────────────────────────────────────────────────────┘   │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Trafego

```
                     Trafego de Entrada (Inference)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   Internet ──▶ API Gateway ──▶ VPC Link ──▶ NLB ──▶ EKS ──▶ Inference Pods    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                     Trafego de Processamento (Process)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   SQS Queue ◀────── Process Pods (polling) ──────▶ DynamoDB / S3               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

### Cluster

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `eks` | `module.eks` | Cluster EKS via modulo oficial |
| `node_sagemaker_mlflow` | `aws_iam_role_policy` | Inline policy para MLflow |
| `node_ec2_full_access` | `aws_iam_role_policy` | Inline policy para EC2 |
| `node_autoscaling_access` | `aws_iam_role_policy` | Inline policy para AutoScaling |

### Recursos do Modulo EKS

| Recurso | Descricao |
|---------|-----------|
| **EKS Cluster** | Control plane gerenciado |
| **Managed Node Group** | Grupo de nodes "general" |
| **IAM Roles** | Roles para cluster e nodes |
| **Security Groups** | SGs para cluster e nodes |
| **OIDC Provider** | Provider para IRSA (desabilitado) |

---

## Node Group

### Configuracao do Node Group "general"

| Atributo | Valor | Descricao |
|----------|-------|-----------|
| **Nome** | `general` | Node group multi-purpose |
| **Instance Types** | `t3.medium` (default) | x86_64 Intel, cost-effective |
| **AMI** | `AL2023_x86_64_STANDARD` | Amazon Linux 2023 |
| **Capacity Type** | `ON_DEMAND` | Latencia previsivel (nao SPOT) |
| **Min Size** | 2 | HA basico |
| **Max Size** | 4 | Auto-scaling moderado |
| **Desired Size** | 2 | Tamanho inicial |

### Disco (EBS)

| Atributo | Valor |
|----------|-------|
| **Device** | `/dev/xvda` |
| **Size** | 50 GB |
| **Type** | gp3 |
| **IOPS** | 3000 |
| **Throughput** | 125 MB/s |
| **Encrypted** | true |

### IAM Policies do Node

O node role possui as seguintes policies:

**Managed Policies (Automaticas do Modulo EKS)**:
- `AmazonEKSWorkerNodePolicy`
- `AmazonEC2ContainerRegistryReadOnly`
- `AmazonEKS_CNI_Policy`

**Managed Policies Adicionais**:

| Policy | Proposito |
|--------|-----------|
| `CloudWatchFullAccess` | Logs e metricas |
| `AmazonSSMManagedInstanceCore` | Session Manager |
| `ElasticLoadBalancingFullAccess` | AWS LB Controller |
| `AmazonKinesisFirehoseFullAccess` | Streaming de dados |
| `AmazonSQSFullAccess` | Process service (SQS) |
| `AmazonS3ReadOnlyAccess` | Leitura de modelos |
| `AmazonDynamoDBFullAccess` | Feature store |

**Inline Policies**:

| Policy | Proposito |
|--------|-----------|
| `SageMakerMLflowFullAccess` | MLflow Model Registry |
| `EC2FullAccess` | AWS LB Controller (ENIs, SGs) |
| `AutoScalingFullAccess` | Cluster Autoscaler |

---

## Addons

### Addons Configurados

| Addon | Before Compute | Descricao |
|-------|----------------|-----------|
| `vpc-cni` | `true` | CNI plugin para networking (nodes precisam) |
| `kube-proxy` | `true` | Network proxy (nodes precisam) |
| `coredns` | `false` | DNS interno (precisa de nodes para rodar) |

### Ordem de Criacao

```
1. vpc-cni      (before_compute = true)  ──┐
2. kube-proxy   (before_compute = true)  ──┼── Criados ANTES dos nodes
                                           │
3. Managed Node Group                    ──┤── Nodes criados
                                           │
4. coredns      (before_compute = false) ──┘── Criado DEPOIS dos nodes
```

> **Importante**: Se `coredns` tiver `before_compute = true`, ele fica `DEGRADED` esperando nodes que ainda nao existem.

### Addon Comentado

```hcl
# aws-ebs-csi-driver = {
#   most_recent = true
#   before_compute = true
# }
```

> O EBS CSI Driver requer IAM Role com IRSA. Sera criado manualmente via `eks create-addon --service-account-role-arn`.

---

## Seguranca

### Endpoint Access

| Endpoint | Valor | Descricao |
|----------|-------|-----------|
| **Public** | `true` | Acesso via kubectl local/CI-CD (com autenticacao) |
| **Private** | `true` | Acesso dos nodes na VPC |

### Security Group Rules

**Cluster Security Group**:

| Tipo | Protocolo | Portas | Origem | Descricao |
|------|-----------|--------|--------|-----------|
| Ingress | TCP | 1025-65535 | Node SG | Ephemeral ports dos nodes |

**Node Security Group**:

| Tipo | Protocolo | Portas | Origem | Descricao |
|------|-----------|--------|--------|-----------|
| Ingress | All | All | Self | Node-to-node communication |
| Egress | All | All | 0.0.0.0/0 | Saida para internet |

### Cluster Creator Admin

```hcl
enable_cluster_creator_admin_permissions = true
```

O IAM principal que criou o cluster tem acesso admin automatico.

---

## Restricoes SCP

A conta AWS possui **Service Control Policies (SCPs)** que bloqueiam certas acoes. O modulo foi ajustado para funcionar com essas restricoes:

### Acoes Bloqueadas pelo SCP

| Acao | Impacto | Workaround |
|------|---------|------------|
| `iam:TagRole` | Nao pode aplicar tags em IAM roles | Tags removidas de roles |
| `iam:CreatePolicy` | Nao pode criar custom policies | Usar apenas AWS managed policies |
| `iam:CreateOpenIDConnectProvider` | Nao pode criar OIDC provider | IRSA desabilitado |

### Configuracoes Ajustadas

```hcl
# Tags desabilitadas
iam_role_tags = {}
tags = {}

# Encryption desabilitada (requer custom policy)
attach_cluster_encryption_policy = false
cluster_encryption_config = {}

# Logging desabilitado (requer custom policy para CloudWatch)
cluster_enabled_log_types = []
create_cloudwatch_log_group = false

# IRSA desabilitado (requer OIDC provider)
enable_irsa = false

# Auto mode tags desabilitadas (requer custom policy)
enable_auto_mode_custom_tags = false
```

### Pods e Permissoes

Sem IRSA, os pods usam as permissoes do **IAM Role do Node** (instance profile). Por isso o node role possui muitas policies anexadas.

---

## Uso

### Uso Basico

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "elo-fraud-cluster-dev"
  cluster_version = "1.32"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  environment = "dev"
}
```

### Uso com Configuracoes Customizadas

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "elo-fraud-cluster-staging"
  cluster_version = "1.32"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Node configuration
  node_instance_types = ["t3.large"]
  node_min_size       = 2
  node_max_size       = 6
  node_desired_size   = 3

  environment = "staging"
}
```

### Uso Completo (Producao)

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "elo-fraud-cluster-prod"
  cluster_version = "1.32"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Node configuration para producao
  node_instance_types = ["m6i.large", "m5.large"]  # Fallback types
  node_min_size       = 3
  node_max_size       = 10
  node_desired_size   = 3

  environment = "prod"
}
```

---

## Variaveis

### Cluster

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `cluster_name` | `string` | Sim | - | Nome do cluster (pattern: `elo-fraud-cluster-{env}`) |
| `cluster_version` | `string` | Nao | `1.32` | Versao do Kubernetes |
| `environment` | `string` | Nao | `dev` | Ambiente (usado para nomear IAM roles) |

### Networking

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `vpc_id` | `string` | Sim | - | ID da VPC |
| `subnet_ids` | `list(string)` | Sim | - | IDs das subnets privadas (minimo 2) |

### Node Group

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `node_instance_types` | `list(string)` | Nao | `["t3.medium"]` | Tipos de instancia |
| `node_min_size` | `number` | Nao | `2` | Minimo de nodes |
| `node_max_size` | `number` | Nao | `4` | Maximo de nodes |
| `node_desired_size` | `number` | Nao | `2` | Quantidade desejada |

### Validacoes

- `cluster_name`: Apenas letras minusculas, numeros e hifens
- `cluster_version`: Deve ser 1.27 ou superior
- `vpc_id`: Deve comecar com `vpc-`
- `subnet_ids`: Minimo de 2 subnets
- `node_min_size`: Minimo 1
- `node_max_size`: Deve ser >= `node_min_size`

---

## Outputs

### Cluster

| Output | Tipo | Descricao |
|--------|------|-----------|
| `cluster_id` | `string` | ID do cluster |
| `cluster_name` | `string` | Nome do cluster |
| `cluster_endpoint` | `string` | URL do API server |
| `cluster_certificate_authority_data` | `string` | CA certificate (sensitive) |
| `cluster_version` | `string` | Versao do Kubernetes |
| `cluster_iam_role_arn` | `string` | ARN da role do cluster |

### Security Groups

| Output | Tipo | Descricao |
|--------|------|-----------|
| `cluster_security_group_id` | `string` | SG do control plane |
| `node_security_group_id` | `string` | SG dos nodes |
| `cluster_primary_security_group_id` | `string` | SG primario do cluster |

### Node Group

| Output | Tipo | Descricao |
|--------|------|-----------|
| `node_group_id` | `string` | ID do node group |
| `node_group_arn` | `string` | ARN do node group |
| `node_group_status` | `string` | Status do node group |
| `node_group_iam_role_arn` | `string` | ARN da role dos nodes |

### OIDC (para IRSA futuro)

| Output | Tipo | Descricao |
|--------|------|-----------|
| `oidc_provider_arn` | `string` | ARN do OIDC provider |
| `oidc_provider_url` | `string` | URL do OIDC provider (sem https://) |

---

## Operacoes

### Configurar kubectl

```bash
# Atualizar kubeconfig
aws eks update-kubeconfig \
  --name elo-fraud-cluster-staging \
  --region sa-east-1

# Verificar conexao
kubectl cluster-info
kubectl get nodes
```

### Verificar Status do Cluster

```bash
# Status do cluster
aws eks describe-cluster \
  --name elo-fraud-cluster-staging \
  --query 'cluster.status' \
  --region sa-east-1

# Status dos addons
aws eks list-addons \
  --cluster-name elo-fraud-cluster-staging \
  --region sa-east-1

# Detalhes de um addon
aws eks describe-addon \
  --cluster-name elo-fraud-cluster-staging \
  --addon-name coredns \
  --region sa-east-1
```

### Verificar Node Group

```bash
# Listar node groups
aws eks list-nodegroups \
  --cluster-name elo-fraud-cluster-staging \
  --region sa-east-1

# Detalhes do node group
aws eks describe-nodegroup \
  --cluster-name elo-fraud-cluster-staging \
  --nodegroup-name general \
  --region sa-east-1

# Ver nodes no Kubernetes
kubectl get nodes -o wide
```

### Escalar Node Group

```bash
# Escalar manualmente
aws eks update-nodegroup-config \
  --cluster-name elo-fraud-cluster-staging \
  --nodegroup-name general \
  --scaling-config minSize=2,maxSize=6,desiredSize=4 \
  --region sa-east-1
```

### Atualizar Addon

```bash
# Atualizar addon para ultima versao
aws eks update-addon \
  --cluster-name elo-fraud-cluster-staging \
  --addon-name coredns \
  --resolve-conflicts OVERWRITE \
  --region sa-east-1
```

### Acessar Node via SSM

```bash
# Listar instancias
aws ec2 describe-instances \
  --filters "Name=tag:eks:nodegroup-name,Values=general" \
  --query 'Reservations[*].Instances[*].[InstanceId,PrivateIpAddress]' \
  --output table \
  --region sa-east-1

# Conectar via Session Manager
aws ssm start-session \
  --target i-xxxxxxxxxxxxxxxxx \
  --region sa-east-1
```

---

## Troubleshooting

### Erro: Nodes nao entram no cluster

**Sintoma**: Nodes ficam em `NotReady` ou nao aparecem.

**Causas possiveis**:
1. VPC CNI addon nao instalado
2. Security group bloqueando comunicacao
3. IAM role sem permissoes

**Solucao**:
```bash
# Verificar status dos addons
aws eks describe-addon \
  --cluster-name elo-fraud-cluster-staging \
  --addon-name vpc-cni \
  --region sa-east-1

# Verificar logs do kubelet (via SSM)
journalctl -u kubelet -f
```

---

### Erro: CoreDNS DEGRADED

**Sintoma**: Addon coredns fica em status DEGRADED.

**Causa**: CoreDNS foi criado antes dos nodes (before_compute = true).

**Solucao**: O modulo ja esta configurado com `before_compute = false`. Se o problema persistir:
```bash
# Reiniciar pods do coredns
kubectl rollout restart deployment/coredns -n kube-system
```

---

### Erro: kubectl unauthorized

**Sintoma**:
```
error: You must be logged in to the server (Unauthorized)
```

**Causa**: Token expirado ou permissoes IAM insuficientes.

**Solucao**:
```bash
# Atualizar kubeconfig
aws eks update-kubeconfig \
  --name elo-fraud-cluster-staging \
  --region sa-east-1

# Verificar identidade
aws sts get-caller-identity
```

---

### Erro: Pods sem acesso a servicos AWS

**Sintoma**: Pods recebem Access Denied ao acessar S3, DynamoDB, etc.

**Causa**: IRSA desabilitado, pods usam role do node.

**Solucao**: Verificar se a policy necessaria esta no node role:
```bash
# Ver policies do node role
aws iam list-attached-role-policies \
  --role-name elo-fraud-eks-node-role-staging

aws iam list-role-policies \
  --role-name elo-fraud-eks-node-role-staging
```

---

### Verificar Saude do Cluster

```bash
# Componentes do control plane
kubectl get componentstatuses

# Pods de sistema
kubectl get pods -n kube-system

# Eventos recentes
kubectl get events --sort-by='.lastTimestamp' -A | tail -20
```

---

## Custos Estimados

### Componentes de Custo (sa-east-1)

| Componente | Calculo | Custo/Mes |
|------------|---------|-----------|
| **Control Plane** | $0.10/hora x 730h | ~$73 |
| **Nodes (2x t3.medium)** | 2 x $0.0336/h x 730h | ~$49 |
| **EBS (2x 50GB gp3)** | 100GB x $0.08/GB | ~$8 |
| **Data Transfer** | Variavel | ~$10 |
| **Total** | - | **~$140/mes** |

### Comparativo por Ambiente

| Ambiente | Nodes | Instance | Custo Estimado |
|----------|-------|----------|----------------|
| **DEV** | 2 | t3.medium | ~$140/mes |
| **STAGING** | 3 | t3.large | ~$250/mes |
| **PROD** | 3-10 | m6i.large | ~$400-800/mes |

> **Nota**: Custos nao incluem ALB, VPC endpoints, NAT Gateway, etc.

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Single node group** | Simplifica operacao, workloads similares |
| **ON_DEMAND capacity** | Latencia previsivel para scoring de fraude |
| **t3.medium (x86_64)** | Melhor custo-beneficio para workloads leves |
| **AL2023 x86_64** | Compatibilidade com imagens existentes |
| **Public + Private endpoint** | Permite kubectl local e comunicacao interna |
| **IRSA desabilitado** | Restricao de SCP, pods usam role do node |
| **before_compute correto** | Evita CoreDNS DEGRADED |

---

## Referencias

- [Amazon EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)
- [terraform-aws-modules/eks](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [EKS Addons](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)

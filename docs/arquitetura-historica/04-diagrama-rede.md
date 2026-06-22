# Diagrama de Rede - ELO Fraud Detection

**VPC:** elo-fraud-vpc-dev
**CIDR:** 10.0.0.0/16
**Região:** us-east-1
**Data:** 2025-11-23

---

## Topologia de Rede Completa

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ AWS REGION: us-east-1                                                                           │
│                                                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ VPC: elo-fraud-vpc-dev                                                                      │ │
│ │ CIDR: 10.0.0.0/16 (65,536 IPs)                                                              │ │
│ │                                                                                             │ │
│ │                         ┌────────────────────────────┐                                      │ │
│ │                         │  Internet Gateway (IGW)    │                                      │ │
│ │                         │  Provides NAT for public   │                                      │ │
│ │                         │  subnet outbound traffic   │                                      │ │
│ │                         └────────────┬───────────────┘                                      │ │
│ │                                      │                                                       │ │
│ │ ┌───────────────────────────────────────────────────────────────────────────────────────┐  │ │
│ │ │ AVAILABILITY ZONE: us-east-1a                                                         │  │ │
│ │ │                                                                                        │  │ │
│ │ │ ┌───────────────────────────────────────────┐                                         │  │ │
│ │ │ │ PUBLIC SUBNET 1                           │                                         │  │ │
│ │ │ │ CIDR: 10.0.1.0/24 (256 IPs)               │                                         │  │ │
│ │ │ │ Auto-assign Public IP: ✅ Yes              │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Resources:                                 │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ Application Load Balancer  │          │                                         │  │ │
│ │ │ │   │ (ALB Nodes)                │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Public IP: x.x.x.x         │          │                                         │  │ │
│ │ │ │   │ Port: 80 (HTTP)            │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Security Group: ALB-SG     │          │                                         │  │ │
│ │ │ │   │   Ingress: 0.0.0.0/0:80    │          │                                         │  │ │
│ │ │ │   │   Ingress: 0.0.0.0/0:443   │          │                                         │  │ │
│ │ │ │   │   Egress: All              │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Route Table: Public-RT                    │                                         │  │ │
│ │ │ │   Destination    │ Target                 │                                         │  │ │
│ │ │ │   10.0.0.0/16    │ local                  │                                         │  │ │
│ │ │ │   0.0.0.0/0      │ igw-xxxx (IGW)         │                                         │  │ │
│ │ │ └───────────────────────────────────────────┘                                         │  │ │
│ │ │                                                                                        │  │ │
│ │ │ ┌───────────────────────────────────────────┐                                         │  │ │
│ │ │ │ PRIVATE SUBNET 1                          │                                         │  │ │
│ │ │ │ CIDR: 10.0.11.0/24 (256 IPs)              │                                         │  │ │
│ │ │ │ Auto-assign Public IP: ❌ No               │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Resources:                                 │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ EKS Worker Nodes           │          │                                         │  │ │
│ │ │ │   │ (EC2 - t3.medium)          │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Private IP: 10.0.11.x      │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Pods Running:              │          │                                         │  │ │
│ │ │ │   │   - inference (10.0.11.50) │          │                                         │  │ │
│ │ │ │   │   - process (10.0.11.51)   │          │                                         │  │ │
│ │ │ │   │   - coredns                │          │                                         │  │ │
│ │ │ │   │   - kube-proxy             │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ VPC Endpoints (Interface)  │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ - ecr.api (10.0.11.10)     │          │                                         │  │ │
│ │ │ │   │ - ecr.dkr (10.0.11.11)     │          │                                         │  │ │
│ │ │ │   │ - logs (10.0.11.12)        │          │                                         │  │ │
│ │ │ │   │ - sqs (10.0.11.13)         │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Private DNS: ✅ Enabled     │          │                                         │  │ │
│ │ │ │   │                            │          │                                         │  │ │
│ │ │ │   │ Security Group: VPCe-SG    │          │                                         │  │ │
│ │ │ │   │   Ingress: 10.0.0.0/16:443 │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Route Table: Private-RT                   │                                         │  │ │
│ │ │ │   Destination    │ Target                 │                                         │  │ │
│ │ │ │   10.0.0.0/16    │ local                  │                                         │  │ │
│ │ │ │   (No default route - isolated)           │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ VPC Endpoints (Gateway - Route Table):    │                                         │  │ │
│ │ │ │   s3 prefix-list │ vpce-s3-xxxx           │                                         │  │ │
│ │ │ │   ddb prefix-list│ vpce-ddb-xxxx          │                                         │  │ │
│ │ │ └───────────────────────────────────────────┘                                         │  │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────┘  │ │
│ │                                                                                             │ │
│ │ ┌───────────────────────────────────────────────────────────────────────────────────────┐  │ │
│ │ │ AVAILABILITY ZONE: us-east-1b                                                         │  │ │
│ │ │                                                                                        │  │ │
│ │ │ ┌───────────────────────────────────────────┐                                         │  │ │
│ │ │ │ PUBLIC SUBNET 2                           │                                         │  │ │
│ │ │ │ CIDR: 10.0.2.0/24 (256 IPs)               │                                         │  │ │
│ │ │ │ Auto-assign Public IP: ✅ Yes              │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Resources:                                 │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ ALB Nodes (HA)             │          │                                         │  │ │
│ │ │ │   │ Public IP: y.y.y.y         │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Route Table: Public-RT (shared)           │                                         │  │ │
│ │ │ └───────────────────────────────────────────┘                                         │  │ │
│ │ │                                                                                        │  │ │
│ │ │ ┌───────────────────────────────────────────┐                                         │  │ │
│ │ │ │ PRIVATE SUBNET 2                          │                                         │  │ │
│ │ │ │ CIDR: 10.0.12.0/24 (256 IPs)              │                                         │  │ │
│ │ │ │ Auto-assign Public IP: ❌ No               │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Resources:                                 │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ EKS Worker Nodes (Standby) │          │                                         │  │ │
│ │ │ │   │ Auto-scales when needed    │          │                                         │  │ │
│ │ │ │   │ Private IP: 10.0.12.x      │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │   ┌────────────────────────────┐          │                                         │  │ │
│ │ │ │   │ VPC Endpoints (HA)         │          │                                         │  │ │
│ │ │ │   │ (Replicated from AZ-1a)    │          │                                         │  │ │
│ │ │ │   └────────────────────────────┘          │                                         │  │ │
│ │ │ │                                           │                                         │  │ │
│ │ │ │ Route Table: Private-RT (shared)          │                                         │  │ │
│ │ │ └───────────────────────────────────────────┘                                         │  │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ NETWORK CONNECTIVITY SUMMARY                                                                │ │
│ │                                                                                             │ │
│ │ Public Subnets → Internet:                                                                  │ │
│ │   ✅ Yes (via Internet Gateway)                                                             │ │
│ │   Used for: ALB (public-facing load balancer)                                              │ │
│ │                                                                                             │ │
│ │ Private Subnets → Internet:                                                                 │ │
│ │   ❌ No NAT Gateway (cost optimization in dev)                                              │ │
│ │   ✅ VPC Endpoints for AWS services instead:                                                │ │
│ │     - S3 (gateway endpoint - free)                                                          │ │
│ │     - DynamoDB (gateway endpoint - free)                                                    │ │
│ │     - ECR API (interface endpoint - $7.20/mo)                                              │ │
│ │     - ECR DKR (interface endpoint - $7.20/mo)                                              │ │
│ │     - CloudWatch Logs (interface endpoint - $7.20/mo)                                      │ │
│ │     - SQS (interface endpoint - $7.20/mo)                                                  │ │
│ │                                                                                             │ │
│ │ Total Monthly VPC Endpoint Cost: ~$28.80 (vs ~$32/mo for NAT Gateway)                      │ │
│ │                                                                                             │ │
│ │ Cross-AZ Traffic:                                                                           │ │
│ │   EKS pods can communicate across AZs via VPC local routing                                │ │
│ │   ALB distributes traffic to both AZs                                                       │ │
│ │                                                                                             │ │
│ │ DNS Resolution:                                                                             │ │
│ │   ✅ DNS Hostnames: Enabled                                                                 │ │
│ │   ✅ DNS Support: Enabled                                                                   │ │
│ │   ✅ VPC Endpoint Private DNS: Enabled                                                      │ │
│ │     (e.g., ecr.us-east-1.amazonaws.com resolves to 10.0.11.10)                             │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detalhamento de Subnets

| Subnet | AZ | CIDR | IPs Disponíveis | Tipo | Recursos |
|--------|-----|------|-----------------|------|----------|
| Public-1 | us-east-1a | 10.0.1.0/24 | 251 | Pública | ALB nodes |
| Public-2 | us-east-1b | 10.0.2.0/24 | 251 | Pública | ALB nodes |
| Private-1 | us-east-1a | 10.0.11.0/24 | 251 | Privada | EKS nodes, VPC endpoints |
| Private-2 | us-east-1b | 10.0.12.0/24 | 251 | Privada | EKS nodes (auto-scale) |

**Total de IPs alocados:** 1004 de 65,536 disponíveis (1.5% utilização)

---

## Route Tables

### Public Route Table

| Destination | Target | Descrição |
|-------------|--------|-----------|
| 10.0.0.0/16 | local | Tráfego interno VPC |
| 0.0.0.0/0 | igw-xxxx | Internet via IGW |

**Subnets associadas:** Public-1, Public-2

### Private Route Table

| Destination | Target | Descrição |
|-------------|--------|-----------|
| 10.0.0.0/16 | local | Tráfego interno VPC |
| pl-xxxxx (S3) | vpce-s3-xxxx | S3 via Gateway Endpoint |
| pl-yyyyy (DDB) | vpce-ddb-xxxx | DynamoDB via Gateway Endpoint |

**Subnets associadas:** Private-1, Private-2

**Observação:** Não há rota default (0.0.0.0/0) → subnets privadas isoladas da internet

---

## Security Groups

### ALB Security Group

```
Name: elo-fraud-alb-sg-dev
VPC: elo-fraud-vpc-dev

Inbound Rules:
  Protocol    Port    Source         Description
  TCP         80      0.0.0.0/0      HTTP from internet
  TCP         443     0.0.0.0/0      HTTPS from internet (commented in dev)

Outbound Rules:
  Protocol    Port    Destination    Description
  All         All     0.0.0.0/0      All traffic allowed
```

### VPC Endpoints Security Group

```
Name: elo-fraud-vpce-sg-dev
VPC: elo-fraud-vpc-dev

Inbound Rules:
  Protocol    Port    Source         Description
  TCP         443     10.0.0.0/16    HTTPS from VPC CIDR

Outbound Rules:
  (None - interface endpoints don't initiate outbound connections)
```

### EKS Node Security Group (Auto-created)

```
Name: eks-cluster-sg-elo-fraud-cluster-dev-xxxxx
VPC: elo-fraud-vpc-dev

Inbound Rules:
  - All traffic from self (node-to-node)
  - HTTPS (443) from EKS control plane
  - Custom from ALB security group (for pod traffic)

Outbound Rules:
  - All traffic to 0.0.0.0/0
```

---

## VPC Endpoints

### Gateway Endpoints (FREE)

| Endpoint | Service | Route Table | Custo |
|----------|---------|-------------|-------|
| vpce-s3-xxxx | com.amazonaws.us-east-1.s3 | Private-RT | $0/mês |
| vpce-ddb-xxxx | com.amazonaws.us-east-1.dynamodb | Private-RT | $0/mês |

**Benefício:** Acesso privado a S3 e DynamoDB sem custos adicionais

### Interface Endpoints (~$7.20/mês cada)

| Endpoint | Service | Subnets | Private DNS | Custo/mês |
|----------|---------|---------|-------------|-----------|
| vpce-ecr-api | com.amazonaws.us-east-1.ecr.api | Private-1, Private-2 | ✅ | $7.20 |
| vpce-ecr-dkr | com.amazonaws.us-east-1.ecr.dkr | Private-1, Private-2 | ✅ | $7.20 |
| vpce-logs | com.amazonaws.us-east-1.logs | Private-1, Private-2 | ✅ | $7.20 |
| vpce-sqs | com.amazonaws.us-east-1.sqs | Private-1, Private-2 | ✅ | $7.20 |

**Total:** $28.80/mês

**Private DNS Enabled:** Sim → URLs públicas (ecr.us-east-1.amazonaws.com) resolvem para IPs privados

---

## Conectividade Externa

### Pods EKS → AWS Services

```
Pods (10.0.11.x)
  ↓
VPC Endpoints (10.0.11.10-13) → Private DNS resolution
  ↓
AWS Services (S3, DynamoDB, ECR, CloudWatch, SQS)
```

**Sem necessidade de:** NAT Gateway, Internet Gateway para pods

### Cliente → API Inference

```
Cliente (Internet/VPC)
  ↓
API Gateway (Regional endpoint)
  ↓
HTTP Proxy
  ↓
ALB (internal scheme - VPC only)
  ↓
Target Group (IP mode)
  ↓
Pod IP (10.0.11.50)
```

---

## Otimizações de Custo Aplicadas

| Item | Opção Padrão | Opção Escolhida | Economia |
|------|--------------|-----------------|----------|
| NAT Gateway | 1x NAT GW | VPC Endpoints | ~$3/mês |
| VPC Link (API GW) | NLB + VPC Link | HTTP Proxy direto | $22/mês |
| Multi-AZ NAT | 2x NAT GW | VPC Endpoints | ~$30/mês |

**Total de economia:** ~$55/mês em rede

---

## Considerações de Segurança

✅ **Implementado:**
- Subnets privadas isoladas (sem rota default)
- VPC Endpoints para comunicação privada
- Security Groups restritivos
- ALB interno (scheme: internal)

⚠️ **Pendente:**
- Network ACLs (usando Security Groups apenas)
- VPC Flow Logs (para auditoria)
- Network Policies no Kubernetes
- WAF no ALB (produção)

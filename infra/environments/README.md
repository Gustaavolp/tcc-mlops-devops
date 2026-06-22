# Environments - Elo Fraud Detection

## Sumario

- [Visao Geral](#visao-geral)
- [Ambientes Disponiveis](#ambientes-disponiveis)
- [Arquitetura de Stacks](#arquitetura-de-stacks)
- [Comparativo de Ambientes](#comparativo-de-ambientes)
- [Estrategia de Deploy](#estrategia-de-deploy)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Remote State](#remote-state)
- [Custos Estimados](#custos-estimados)
- [Guia de Uso](#guia-de-uso)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este diretorio contem as configuracoes Terraform organizadas por ambiente. Cada ambiente possui infraestrutura isolada e independente, permitindo desenvolvimento, testes e producao sem interferencia entre eles.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Isolamento** | Ambientes completamente separados por regiao e VPC |
| **Consistencia** | Mesma estrutura de stacks em todos os ambientes |
| **Rastreabilidade** | State files separados por ambiente e stack |
| **Promocao** | Pipeline de codigo dev → staging → prod |

### Principios de Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRINCIPIOS DE DESIGN                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ISOLAMENTO          2. STACKS              3. REMOTE STATE              │
│  ┌───────────┐          INDEPENDENTES          ┌───────────┐               │
│  │    DEV    │          ┌─────────┐           │  S3 + Native│               │
│  │ us-east-1 │          │Foundation│───┐      │    Locking  │               │
│  └───────────┘          └─────────┘   │      └───────────┘               │
│  ┌───────────┐          ┌─────────┐   │                                    │
│  │  STAGING  │          │  MLOps  │───┼──▶ Blast radius reduzido          │
│  │ sa-east-1 │          └─────────┘   │                                    │
│  └───────────┘          ┌─────────┐   │                                    │
│  ┌───────────┐          │Platform │───┘                                    │
│  │   PROD    │          └─────────┘                                        │
│  │ sa-east-1 │                                                              │
│  └───────────┘                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Ambientes Disponiveis

### Resumo

| Ambiente | Regiao | VPC CIDR | Proposito | Status |
|----------|--------|----------|-----------|--------|
| **[dev](./dev/)** | us-east-1 | 10.0.0.0/16 | Desenvolvimento e testes | Ativo |
| **[staging](./staging/)** | sa-east-1 | 10.1.0.0/16 | Pre-producao e homologacao | Ativo |
| **prod** | sa-east-1 | 10.2.0.0/16 | Producao | Planejado |

### DEV

Ambiente de desenvolvimento otimizado para **custo** e **agilidade**.

| Caracteristica | Valor |
|----------------|-------|
| **Regiao** | us-east-1 (N. Virginia) |
| **Proposito** | Desenvolvimento, CI/CD, experimentacao |
| **EKS Nodes** | 1-3 (t3.medium) |
| **HPA Inference** | 2-6 pods |
| **Seguranca** | Basica (HTTP, sem WAF) |
| **Custo** | ~$256/mes |

### STAGING

Ambiente de pre-producao na **regiao Brasil** para validacao de performance.

| Caracteristica | Valor |
|----------------|-------|
| **Regiao** | sa-east-1 (Sao Paulo) |
| **Proposito** | Homologacao, testes de carga, validacao |
| **Target** | 100 RPS, p95 < 500ms |
| **EKS Nodes** | 1-5 (t3.medium) |
| **HPA Inference** | 8-12 pods |
| **Seguranca** | Basica (HTTP, sem WAF) |
| **Custo** | ~$301/mes |

### PROD (Planejado)

Ambiente de producao com **alta disponibilidade** e **seguranca**.

| Caracteristica | Valor |
|----------------|-------|
| **Regiao** | sa-east-1 (Sao Paulo) |
| **Proposito** | Producao, clientes reais |
| **Target** | 1000+ RPS, p99 < 500ms |
| **EKS Nodes** | 3-10 (t3.large) |
| **Seguranca** | Completa (HTTPS, WAF, KMS CMK) |
| **Custo** | ~$800-1200/mes (estimado) |

---

## Arquitetura de Stacks

Cada ambiente e composto por **5 stacks Terraform independentes**, cada uma com seu proprio state file.

### Diagrama de Stacks

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            AMBIENTE (dev/staging/prod)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  FOUNDATION                                                         │    │
│   │  ├── VPC (subnets publicas e privadas)                             │    │
│   │  ├── S3 Buckets (7: raw, processed, models, logs, resources, reports) │    │
│   │  ├── VPC Endpoints (S3, DynamoDB, ECR, SQS, etc.)                  │    │
│   │  └── Security Groups base                                           │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                          │                                                   │
│           ┌──────────────┴──────────────┐                                   │
│           ▼                             ▼                                   │
│   ┌───────────────────┐    ┌────────────────────────────────────────────┐  │
│   │  MLOPS            │    │  PLATFORM                                   │  │
│   │  ├── MLflow       │    │  ├── EKS Cluster                           │  │
│   │  └── SageMaker    │    │  ├── ALB + NLB                             │  │
│   │      Studio       │    │  ├── API Gateway + VPC Link                │  │
│   └───────────────────┘    │  ├── DynamoDB + SQS                        │  │
│                            │  ├── ECR Repositories                       │  │
│                            │  ├── Kinesis Firehose                       │  │
│                            │  └── Athena + Glue                          │  │
│                            └───────────────────────┬────────────────────┘  │
│                                                     │                       │
│                                                     ▼                       │
│                            ┌────────────────────────────────────────────┐  │
│                            │  PLATFORM-K8S                               │  │
│                            │  ├── Helm Charts (Metrics Server, KEDA)    │  │
│                            │  ├── ConfigMaps                             │  │
│                            │  ├── HPA + ScaledObject                     │  │
│                            │  └── PDBs + TargetGroupBinding              │  │
│                            └───────────────────────┬────────────────────┘  │
│                                                     │                       │
│                                                     ▼                       │
│                            ┌────────────────────────────────────────────┐  │
│                            │  PLATFORM-LAMBDAS                           │  │
│                            │  └── register-best-model (container)        │  │
│                            └────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Responsabilidades das Stacks

| Stack | Responsabilidade | Ciclo de Mudanca |
|-------|------------------|------------------|
| **foundation** | Rede e armazenamento base | Raro |
| **mlops** | Ferramentas de ML (MLflow, SageMaker) | Ocasional |
| **platform** | Aplicacao principal (EKS, API, Storage) | Frequente |
| **platform-k8s** | Recursos Kubernetes | Frequente |
| **platform-lambdas** | Funcoes Lambda | Ocasional |

### Beneficios da Divisao

| Beneficio | Descricao |
|-----------|-----------|
| **Blast Radius** | Erros em uma stack nao afetam as outras |
| **Tempo de Apply** | Stacks menores aplicam mais rapido |
| **Permissoes** | Times diferentes podem ter acesso a stacks diferentes |
| **Ciclo de Vida** | Foundation muda raramente, Platform frequentemente |
| **State Lock** | Deploys paralelos em stacks diferentes |

---

## Comparativo de Ambientes

### Infraestrutura

| Recurso | DEV | STAGING | PROD (Planejado) |
|---------|-----|---------|------------------|
| **Regiao** | us-east-1 | sa-east-1 | sa-east-1 |
| **VPC CIDR** | 10.0.0.0/16 | 10.1.0.0/16 | 10.2.0.0/16 |
| **AZs** | 2 | 2 | 3 |
| **NAT Gateway** | Desabilitado | Desabilitado | Habilitado |
| **VPC Endpoints** | 11 | 11 | 11 |

### Compute

| Recurso | DEV | STAGING | PROD (Planejado) |
|---------|-----|---------|------------------|
| **EKS Version** | 1.32 | 1.32 | 1.32 |
| **Node Type** | t3.medium | t3.medium | t3.large |
| **Node Min/Max** | 1/3 | 1/5 | 3/10 |
| **HPA Min/Max** | 2/6 | 8/12 | 15/30 |
| **HPA CPU Target** | 50% | 35% | 30% |
| **KEDA Max** | 5 | 10 | 20 |

### Seguranca

| Recurso | DEV | STAGING | PROD (Planejado) |
|---------|-----|---------|------------------|
| **HTTPS/TLS** | Nao | Nao | Sim |
| **WAF** | Nao | Nao | Sim |
| **KMS** | AWS Managed | AWS Managed | Customer Managed |
| **Deletion Protection** | Nao | Nao | Sim |

### Performance Targets

| Metrica | DEV | STAGING | PROD (Planejado) |
|---------|-----|---------|------------------|
| **RPS** | N/A | 100 | 1000+ |
| **Latencia p95** | N/A | < 500ms | < 500ms |
| **Latencia p99** | N/A | N/A | < 1000ms |
| **Uptime** | Best effort | 99% | 99.9% |

---

## Estrategia de Deploy

### Ordem de Implantacao por Ambiente

```
1. bootstrap (centralizado - us-east-1)
       │
       ├─────────────────────────────────────────────────────┐
       ▼                                                     ▼
   DEV (us-east-1)                                    STAGING (sa-east-1)
       │                                                     │
       ▼                                                     ▼
   foundation ──┬──▶ mlops                            foundation ──┬──▶ mlops
               │                                                  │
               └──▶ platform                                     └──▶ platform
                        │                                                │
                        ▼                                                ▼
                   platform-k8s                                    platform-k8s
                        │                                                │
                        ▼                                                ▼
                   platform-lambdas                                platform-lambdas
```

### Pipeline de Promocao de Codigo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PIPELINE DE PROMOCAO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Feature Branch ──▶ Pull Request ──▶ Merge to main                        │
│                                              │                              │
│                                              ▼                              │
│                                     ┌───────────────┐                      │
│                                     │   CI/CD DEV   │                      │
│                                     │  (Automatico) │                      │
│                                     └───────┬───────┘                      │
│                                             │                              │
│                                             ▼                              │
│                                     ┌───────────────┐                      │
│                                     │  Testes DEV   │                      │
│                                     │   Passaram?   │                      │
│                                     └───────┬───────┘                      │
│                                             │ Sim                          │
│                                             ▼                              │
│                                     ┌───────────────┐                      │
│                                     │ Deploy STAGING│                      │
│                                     │  (Manual/Tag) │                      │
│                                     └───────┬───────┘                      │
│                                             │                              │
│                                             ▼                              │
│                                     ┌───────────────┐                      │
│                                     │Testes de Carga│                      │
│                                     │  Homologacao  │                      │
│                                     └───────┬───────┘                      │
│                                             │ Aprovado                     │
│                                             ▼                              │
│                                     ┌───────────────┐                      │
│                                     │  Deploy PROD  │                      │
│                                     │(Manual+Approval)│                    │
│                                     └───────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quando Usar Cada Ambiente

| Cenario | Ambiente |
|---------|----------|
| Desenvolvimento de features | DEV |
| Debug e troubleshooting | DEV |
| Experimentacao ML | DEV (MLOps) |
| Code review e PR | DEV |
| Testes de integracao | DEV |
| Testes de carga | STAGING |
| Validacao de performance | STAGING |
| Homologacao com cliente | STAGING |
| UAT (User Acceptance Testing) | STAGING |
| Clientes reais | PROD |

---

## Estrutura de Arquivos

```
infra/environments/
├── README.md                    # Esta documentacao
│
├── dev/                         # Ambiente DEV
│   ├── README.md               # Documentacao do ambiente
│   ├── terraform.tfvars.example # Exemplo de variaveis
│   ├── foundation/             # Stack foundation
│   │   ├── backend.tf
│   │   ├── providers.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── README.md
│   ├── mlops/                  # Stack mlops
│   │   ├── backend.tf
│   │   ├── providers.tf
│   │   ├── data.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── platform/               # Stack platform
│   │   ├── backend.tf
│   │   ├── providers.tf
│   │   ├── data.tf
│   │   ├── *.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── platform-k8s/           # Stack platform-k8s
│   │   ├── backend.tf
│   │   ├── providers.tf
│   │   ├── data.tf
│   │   ├── *.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── platform-lambdas/       # Stack platform-lambdas
│       ├── backend.tf
│       ├── providers.tf
│       ├── data.tf
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
│
└── staging/                     # Ambiente STAGING
    ├── README.md               # Documentacao do ambiente
    ├── terraform.tfvars.example # Exemplo de variaveis
    ├── foundation/             # (mesma estrutura de dev)
    ├── mlops/
    ├── platform/
    ├── platform-k8s/
    └── platform-lambdas/
```

---

## Remote State

### Arquitetura de State

Todos os state files sao armazenados em um bucket S3 centralizado na regiao us-east-1, com locking nativo do S3.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   S3 Bucket: elo-fraud-terraform-state-888577064416-us-east-1               │
│   Region: us-east-1                                                          │
│   Locking: S3 Native (use_lockfile = true)                                  │
│                                                                              │
│   ├── dev/                                                                   │
│   │   ├── foundation/terraform.tfstate                                      │
│   │   ├── mlops/terraform.tfstate                                           │
│   │   ├── platform/terraform.tfstate                                        │
│   │   ├── platform-k8s/terraform.tfstate                                    │
│   │   └── platform-lambdas/terraform.tfstate                                │
│   │                                                                          │
│   └── staging/                                                               │
│       ├── foundation/terraform.tfstate                                      │
│       ├── mlops/terraform.tfstate                                           │
│       ├── platform/terraform.tfstate                                        │
│       ├── platform-k8s/terraform.tfstate                                    │
│       └── platform-lambdas/terraform.tfstate                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Configuracao Backend

Exemplo de configuracao de backend (todas as stacks seguem este padrao):

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "dev/foundation/terraform.tfstate"  # Varia por ambiente/stack
    region       = "us-east-1"
    use_lockfile = true
  }
}
```

### Remote State Data Source

Stacks dependentes consomem outputs via `terraform_remote_state`:

```hcl
# data.tf (exemplo em platform)
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

# Uso
vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id
```

---

## Custos Estimados

### Resumo por Ambiente

| Ambiente | Custo Mensal | Observacao |
|----------|--------------|------------|
| **DEV** | ~$256 | Otimizado para custo |
| **STAGING** | ~$301 | Capacidade aumentada |
| **PROD** | ~$800-1200 | Alta disponibilidade (estimado) |
| **Total** | **~$1357-1757** | Todos os ambientes |

### Detalhamento DEV vs STAGING

| Servico | DEV | STAGING |
|---------|-----|---------|
| EKS Control Plane | $73 | $73 |
| EC2 (nodes) | ~$30 | ~$30-150 |
| ALB | ~$16 | ~$18 |
| NLB | ~$18 | ~$20 |
| VPC Endpoints | ~$35 | ~$40 |
| S3 | ~$5 | ~$5 |
| MLflow | ~$35 | ~$40 |
| DynamoDB | ~$2 | ~$5 |
| Outros | ~$42 | ~$45 |
| **Total** | **~$256** | **~$301** |

### Otimizacoes Aplicadas

| Otimizacao | Economia |
|------------|----------|
| NAT Gateway desabilitado | ~$64/mes (2 ambientes) |
| VPC Endpoints (vs NAT) | Custo previsivel |
| EKS nodes minimos | Escala sob demanda |
| DynamoDB on-demand | Pay-per-use |
| Studio idle shutdown | Variavel |

---

## Guia de Uso

### Pre-requisitos

```bash
# Verificar versoes
terraform --version  # >= 1.10.0
aws --version        # v2.x
kubectl version      # Para platform-k8s

# Configurar credenciais
export AWS_PROFILE=elo
aws sts get-caller-identity
```

### Implantar Ambiente Completo

```bash
# DEV
cd infra/environments/dev
for stack in foundation mlops platform platform-k8s platform-lambdas; do
  echo "=== Applying $stack ==="
  cd $stack && terraform init && terraform apply -auto-approve && cd ..
done

# STAGING
cd infra/environments/staging
for stack in foundation mlops platform platform-k8s platform-lambdas; do
  echo "=== Applying $stack ==="
  cd $stack && terraform init && terraform apply -auto-approve && cd ..
done
```

### Destruir Ambiente Completo

**ATENCAO:** Ordem inversa!

```bash
cd infra/environments/dev  # ou staging

for stack in platform-lambdas platform-k8s platform mlops foundation; do
  echo "=== Destroying $stack ==="
  cd $stack && terraform destroy -auto-approve && cd ..
done
```

### Verificar Status de Todas as Stacks

```bash
cd infra/environments/dev  # ou staging

for stack in foundation mlops platform platform-k8s platform-lambdas; do
  echo "=== $stack ==="
  cd $stack
  terraform state list 2>/dev/null | wc -l | xargs -I {} echo "Resources: {}"
  cd ..
done
```

---

## Troubleshooting

### Erro: Remote state nao encontrado

**Sintoma:**
```
Error: Unable to find remote state
```

**Causa:** Stack dependente nao foi aplicada.

**Solucao:**
```bash
# Verificar ordem de dependencia
# foundation → mlops/platform → platform-k8s → platform-lambdas

# Aplicar stack dependente primeiro
cd ../foundation
terraform apply
```

### Erro: State lock

**Sintoma:**
```
Error: Error acquiring the state lock
```

**Causa:** Outro processo esta usando o state.

**Solucao:**
```bash
# Aguardar o outro processo terminar
# OU (se travado)
terraform force-unlock LOCK_ID
```

### Erro: CIDR conflitante

**Sintoma:**
```
Error: InvalidVpcRange
```

**Causa:** CIDR ja em uso na conta.

**Solucao:**
- DEV: 10.0.0.0/16
- STAGING: 10.1.0.0/16
- PROD: 10.2.0.0/16

### Erro: Recursos em uso entre stacks

**Sintoma:**
```
Error: Resource still in use
```

**Causa:** Tentando destruir stack com dependentes ativos.

**Solucao:**
```bash
# Destruir na ordem inversa
# platform-lambdas → platform-k8s → platform → mlops → foundation
```

---

## Documentacao dos Ambientes

Para documentacao detalhada de cada ambiente, consulte:

| Ambiente | README |
|----------|--------|
| DEV | [dev/README.md](./dev/README.md) |
| STAGING | [staging/README.md](./staging/README.md) |

Para documentacao de cada stack dentro de um ambiente, consulte os READMEs nas respectivas pastas.


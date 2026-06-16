# Modulo NLB (Network Load Balancer)

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Fluxo de Trafego](#fluxo-de-trafego)
- [Uso](#uso)
  - [Uso Basico](#uso-basico)
  - [Uso Completo](#uso-completo)
- [Variaveis](#variaveis)
  - [Identificacao](#identificacao)
  - [Rede](#rede)
  - [Target ALB](#target-alb)
  - [Listener](#listener)
  - [Health Check](#health-check)
  - [Atributos NLB](#atributos-nlb)
  - [Tags](#tags)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)
- [Custos Estimados](#custos-estimados)
- [Decisoes de Arquitetura](#decisoes-de-arquitetura)
- [Referencias](#referencias)

---

## Visao Geral

| Item | Descricao |
|------|-----------|
| **Proposito** | Criar Network Load Balancer interno para integracao com VPC Link do API Gateway |
| **Provider** | AWS (ELB v2) |
| **Tipo** | Network Load Balancer (Layer 4) |
| **Modo** | Interno (private) - obrigatorio para VPC Link |
| **Target Type** | ALB (encaminha trafego para Application Load Balancer) |

### Caracteristicas Principais

| Caracteristica | Descricao |
|----------------|-----------|
| **NLB Interno** | Obrigatorio para integracao com VPC Link do API Gateway |
| **Target Type ALB** | Encaminha trafego diretamente para ALB interno |
| **Cross-Zone Load Balancing** | Distribui trafego entre todas as AZs |
| **Health Check HTTP** | Verifica saude do ALB via HTTP |
| **Layer 4** | Opera na camada de transporte (TCP) |
| **Alta Performance** | Milhoes de requests por segundo, latencia ultra baixa |

---

## Arquitetura

```
                     API Gateway (REST/HTTP)
                              |
                              v
                   +-------------------+
                   |    VPC Link       |
                   | (Private Link)    |
                   +-------------------+
                              |
                              v
          +-------------------------------------------+
          |                  VPC                      |
          |                                           |
          |    +-----------------------------+        |
          |    |   Network Load Balancer     |        |
          |    |       (Interno)             |        |
          |    |   - TCP Listener (:80)      |        |
          |    |   - Cross-Zone Enabled      |        |
          |    +-----------------------------+        |
          |                   |                       |
          |                   v                       |
          |    +-----------------------------+        |
          |    |      Target Group           |        |
          |    |    (target_type: alb)       |        |
          |    |   - Health Check HTTP       |        |
          |    +-----------------------------+        |
          |                   |                       |
          |                   v                       |
          |    +-----------------------------+        |
          |    | Application Load Balancer   |        |
          |    |       (Interno)             |        |
          |    +-----------------------------+        |
          |                   |                       |
          |                   v                       |
          |    +-----------------------------+        |
          |    |         EKS Pods            |        |
          |    |    (Aplicacao/API)          |        |
          |    +-----------------------------+        |
          |                                           |
          +-------------------------------------------+
```

### Diagrama de Componentes AWS

```
+----------------+     +----------------+     +----------------+
|                |     |                |     |                |
|  API Gateway   |---->|   VPC Link     |---->|      NLB       |
|   (Regional)   |     | (PrivateLink)  |     |   (internal)   |
|                |     |                |     |                |
+----------------+     +----------------+     +--------+-------+
                                                       |
                                                       | TCP :80
                                                       v
                                              +--------+-------+
                                              |                |
                                              |  Target Group  |
                                              | (type: alb)    |
                                              |                |
                                              +--------+-------+
                                                       |
                                                       | HTTP :80
                                                       v
                                              +--------+-------+
                                              |                |
                                              |      ALB       |
                                              |   (internal)   |
                                              |                |
                                              +--------+-------+
                                                       |
                                                       v
                                              +--------+-------+
                                              |   EKS Pods     |
                                              +----------------+
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_lb.this` | Network Load Balancer | NLB interno para receber trafego do VPC Link |
| `aws_lb_target_group.this` | Target Group | Target Group tipo ALB para encaminhar ao ALB |
| `aws_lb_target_group_attachment.alb` | Target Attachment | Registro do ALB como target |
| `aws_lb_listener.this` | Listener TCP | Listener na porta especificada (padrao 80) |

### Detalhamento dos Recursos

#### Network Load Balancer
```hcl
resource "aws_lb" "this" {
  name               = var.name
  internal           = true  # SEMPRE interno para VPC Link
  load_balancer_type = "network"
  subnets            = var.subnet_ids

  enable_cross_zone_load_balancing = var.enable_cross_zone_load_balancing
  enable_deletion_protection       = var.enable_deletion_protection
}
```

#### Target Group (tipo ALB)
```hcl
resource "aws_lb_target_group" "this" {
  name        = var.target_group_name
  port        = var.target_port
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "alb"  # Target e o ALB interno

  health_check {
    protocol = "HTTP"
    path     = var.health_check_path
  }
}
```

---

## Fluxo de Trafego

### Request Flow

```
1. Cliente faz request para API Gateway
   |
   v
2. API Gateway roteia via VPC Link (PrivateLink)
   |
   v
3. NLB recebe na porta TCP (80)
   |
   v
4. NLB encaminha para Target Group
   |
   v
5. Target Group direciona para ALB
   |
   v
6. ALB roteia para EKS Pods
   |
   v
7. Resposta retorna pelo mesmo caminho
```

### Por que NLB + ALB?

| Aspecto | Motivo |
|---------|--------|
| **VPC Link** | API Gateway VPC Link requer NLB (nao suporta ALB diretamente) |
| **Funcionalidades ALB** | ALB oferece path-based routing, host-based routing, etc |
| **Arquitetura** | NLB atua como "ponte" entre API Gateway e ALB interno |
| **Performance** | NLB oferece latencia minima na passagem do trafego |

---

## Uso

### Uso Basico

```hcl
module "nlb" {
  source = "./modules/nlb"

  project_name      = "meu-projeto"
  environment       = "dev"
  name              = "meu-projeto-nlb-dev"
  target_group_name = "meu-projeto-nlb-tg-dev"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  alb_arn = module.alb.alb_arn
}

# Criar VPC Link usando o NLB
resource "aws_apigatewayv2_vpc_link" "this" {
  name               = "meu-projeto-vpc-link-dev"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = module.vpc.private_subnet_ids
}
```

### Uso Completo

```hcl
module "nlb" {
  source = "./modules/nlb"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "prod"
  name         = "elo-fraud-api-nlb-prod"  # Nome customizado

  # Rede
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids  # Minimo 2 AZs

  # Target (ALB)
  alb_arn           = module.alb.alb_arn
  target_group_name = "elo-fraud-nlb-to-alb-prod"
  target_port       = 80

  # Listener
  listener_port = 80

  # Health Check
  health_check_path     = "/health"
  health_check_interval = 30
  health_check_timeout  = 10
  healthy_threshold     = 3
  unhealthy_threshold   = 3

  # Atributos NLB
  enable_cross_zone_load_balancing = true
  enable_deletion_protection       = true  # Recomendado para producao

  # Tags
  tags = {
    Team      = "platform"
    CostCenter = "infrastructure"
  }
}

# VPC Link para API Gateway
resource "aws_apigatewayv2_vpc_link" "main" {
  name               = "elo-fraud-vpc-link-prod"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = module.vpc.private_subnet_ids

  tags = {
    Name        = "elo-fraud-vpc-link-prod"
    Environment = "prod"
  }
}

# Integracao API Gateway com VPC Link
resource "aws_apigatewayv2_integration" "nlb" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "HTTP_PROXY"
  integration_uri  = module.alb.listener_arn

  integration_method = "ANY"
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.main.id
}

# Outputs
output "nlb_arn" {
  value = module.nlb.nlb_arn
}

output "nlb_dns_name" {
  value = module.nlb.nlb_dns_name
}
```

### Uso com API Gateway REST

```hcl
# Para API Gateway REST (v1), usar VPC Link diferente
resource "aws_api_gateway_vpc_link" "this" {
  name        = "elo-fraud-vpc-link-rest-prod"
  target_arns = [module.nlb.nlb_arn]  # ARN do NLB

  tags = {
    Name        = "elo-fraud-vpc-link-rest-prod"
    Environment = "prod"
  }
}

# Integracao REST API com VPC Link
resource "aws_api_gateway_integration" "nlb" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "ANY"
  uri                     = "http://${module.nlb.nlb_dns_name}:80/{proxy}"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.this.id
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `project_name` | `string` | Sim | - | Nome do projeto |
| `environment` | `string` | Sim | - | Ambiente (dev, staging, prod) |
| `name` | `string` | Sim | - | Nome do NLB |

### Rede

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `vpc_id` | `string` | Sim | - | ID da VPC onde o NLB sera criado |
| `subnet_ids` | `list(string)` | Sim | - | Lista de IDs de subnets PRIVADAS (minimo 2 AZs recomendado) |

### Target ALB

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `alb_arn` | `string` | Sim | - | ARN do ALB que sera o target do NLB |
| `target_group_name` | `string` | Sim | - | Nome do Target Group |
| `target_port` | `number` | Nao | `80` | Porta do ALB para encaminhar trafego |

### Listener

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `listener_port` | `number` | Nao | `80` | Porta do listener NLB |

### Health Check

| Variavel | Tipo | Obrigatorio | Default | Validacao | Descricao |
|----------|------|-------------|---------|-----------|-----------|
| `health_check_path` | `string` | Nao | `/health` | - | Path para health check HTTP no ALB |
| `health_check_interval` | `number` | Nao | `30` | 10-300 | Intervalo entre health checks (segundos) |
| `health_check_timeout` | `number` | Nao | `10` | 2-120 | Timeout do health check (segundos) |
| `healthy_threshold` | `number` | Nao | `3` | 2-10 | Checks consecutivos para healthy |
| `unhealthy_threshold` | `number` | Nao | `3` | 2-10 | Checks consecutivos para unhealthy |

### Atributos NLB

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `enable_cross_zone_load_balancing` | `bool` | Nao | `true` | Habilitar balanceamento cross-zone |
| `enable_deletion_protection` | `bool` | Nao | `false` | Protecao contra delecao acidental |

### Tags

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `tags` | `map(string)` | Nao | `{}` | Tags adicionais para os recursos |

---

## Outputs

### NLB

| Output | Tipo | Descricao |
|--------|------|-----------|
| `nlb_id` | `string` | ID do Network Load Balancer |
| `nlb_arn` | `string` | ARN do NLB (usado para criar VPC Link) |
| `nlb_arn_suffix` | `string` | ARN suffix do NLB (para metricas CloudWatch) |
| `nlb_dns_name` | `string` | DNS name do NLB |
| `nlb_zone_id` | `string` | Zone ID do NLB (para Route53) |

### Target Group

| Output | Tipo | Descricao |
|--------|------|-----------|
| `target_group_id` | `string` | ID do Target Group |
| `target_group_arn` | `string` | ARN do Target Group |
| `target_group_arn_suffix` | `string` | ARN suffix do Target Group (para metricas) |
| `target_group_name` | `string` | Nome do Target Group |

### Listener

| Output | Tipo | Descricao |
|--------|------|-----------|
| `listener_arn` | `string` | ARN do Listener TCP |
| `listener_id` | `string` | ID do Listener TCP |

### Summary

| Output | Tipo | Descricao |
|--------|------|-----------|
| `nlb_summary` | `object` | Resumo completo da configuracao do NLB |

---

## Operacoes

### Verificar Status do NLB

```bash
# Listar NLBs
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?Type=='network']" \
  --output table

# Detalhes de um NLB especifico
aws elbv2 describe-load-balancers \
  --names "meu-projeto-nlb-dev" \
  --output json

# Verificar atributos do NLB
aws elbv2 describe-load-balancer-attributes \
  --load-balancer-arn "arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/net/meu-nlb/abc123"
```

### Verificar Target Group

```bash
# Listar Target Groups do NLB
aws elbv2 describe-target-groups \
  --load-balancer-arn "arn:aws:elasticloadbalancing:..." \
  --output table

# Verificar saude dos targets
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:...:targetgroup/meu-tg/abc123" \
  --output table
```

### Verificar VPC Link

```bash
# Listar VPC Links (HTTP API)
aws apigatewayv2 get-vpc-links

# Listar VPC Links (REST API)
aws apigateway get-vpc-links

# Detalhes do VPC Link
aws apigateway get-vpc-link --vpc-link-id "abc123"
```

### Metricas CloudWatch

```bash
# Metricas do NLB
aws cloudwatch get-metric-statistics \
  --namespace AWS/NetworkELB \
  --metric-name ActiveFlowCount \
  --dimensions Name=LoadBalancer,Value=net/meu-nlb/abc123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average

# Metricas de Health Check
aws cloudwatch get-metric-statistics \
  --namespace AWS/NetworkELB \
  --metric-name HealthyHostCount \
  --dimensions Name=TargetGroup,Value=targetgroup/meu-tg/abc123 \
              Name=LoadBalancer,Value=net/meu-nlb/def456 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average
```

### Testar Conectividade

```bash
# Testar NLB internamente (de dentro da VPC)
curl -v http://<nlb-dns-name>:80/health

# Testar via API Gateway
curl -v https://<api-gateway-url>/health

# Verificar resolucao DNS do NLB
nslookup <nlb-dns-name>
```

---

## Troubleshooting

### Target Unhealthy

**Sintoma**: Target Group mostra ALB como unhealthy

**Diagnostico**:
```bash
# Verificar saude do target
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:..." \
  --output json

# Verificar se ALB esta respondendo
curl -v http://<alb-dns-name>:80/health
```

**Causas Comuns**:
1. ALB nao responde no path do health check
2. Security Group do ALB nao permite trafego do NLB
3. ALB nao tem targets healthy

**Solucoes**:
- Verificar endpoint de health no ALB
- Verificar Security Groups entre NLB e ALB
- Verificar saude dos targets do ALB

### VPC Link nao Funciona

**Sintoma**: API Gateway retorna erro 500 ou timeout

**Diagnostico**:
```bash
# Verificar status do VPC Link
aws apigateway get-vpc-link --vpc-link-id "abc123"

# Verificar se NLB esta disponivel
aws elbv2 describe-load-balancers --names "meu-nlb" \
  --query "LoadBalancers[0].State" --output text
```

**Causas Comuns**:
1. NLB nao e interno (VPC Link requer NLB interno)
2. Subnets do VPC Link diferentes das subnets do NLB
3. Security Groups bloqueando trafego

**Solucoes**:
- Verificar que NLB e `internal = true`
- Usar mesmas subnets privadas para NLB e VPC Link
- Verificar Security Groups

### Latencia Alta

**Sintoma**: Requests via API Gateway tem latencia elevada

**Diagnostico**:
```bash
# Metricas de latencia do NLB
aws cloudwatch get-metric-statistics \
  --namespace AWS/NetworkELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=net/meu-nlb/abc123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics p95
```

**Causas Comuns**:
1. Cross-zone load balancing desabilitado
2. Aplicacao lenta
3. Health checks muito agressivos

**Solucoes**:
- Habilitar `enable_cross_zone_load_balancing = true`
- Verificar performance da aplicacao
- Ajustar intervalos de health check

### Conexoes Dropadas

**Sintoma**: Conexoes sendo resetadas

**Diagnostico**:
```bash
# Verificar metricas de conexao
aws cloudwatch get-metric-statistics \
  --namespace AWS/NetworkELB \
  --metric-name TCP_Client_Reset_Count \
  --dimensions Name=LoadBalancer,Value=net/meu-nlb/abc123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum
```

**Causas Comuns**:
1. Idle timeout muito baixo
2. Targets nao preparados para novas conexoes
3. Problemas de rede

---

## Custos Estimados

### Componentes de Custo

| Componente | Preco (us-east-1) | Observacao |
|------------|-------------------|------------|
| NLB por hora | ~$0.0225/hora | ~$16.20/mes |
| LCU (Load Balancer Capacity Unit) | ~$0.006/LCU/hora | Baseado em uso |
| Dados processados | Incluido no LCU | - |

### Estimativa Mensal

| Cenario | NLB Hora | LCU Estimado | Total Estimado |
|---------|----------|--------------|----------------|
| Desenvolvimento | $16.20 | ~$5 | ~$21/mes |
| Staging | $16.20 | ~$10 | ~$26/mes |
| Producao (baixo) | $16.20 | ~$30 | ~$46/mes |
| Producao (alto) | $16.20 | ~$100 | ~$116/mes |

### LCU - Dimensoes

O custo de LCU e calculado pela maior das dimensoes:
- **Novas conexoes**: 800/segundo por LCU
- **Conexoes ativas**: 100.000 por LCU
- **Bytes processados**: 1 GB/hora para TCP

> **Nota**: NLB e significativamente mais barato que ALB para casos de uso simples.

---

## Decisoes de Arquitetura

### Por que NLB Interno?

| Decisao | NLB Interno |
|---------|-------------|
| **Motivo** | VPC Link do API Gateway requer NLB privado |
| **Beneficio** | Trafego nunca sai da rede AWS |
| **Trade-off** | NLB nao acessivel diretamente da internet |

### Por que Target Type ALB?

| Decisao | Target Type = ALB |
|---------|-------------------|
| **Motivo** | Combinar NLB (para VPC Link) com funcionalidades do ALB |
| **Beneficio** | Permite usar path-based routing, host-based routing |
| **Trade-off** | Adiciona um hop extra (latencia minima) |
| **Alternativa** | Target Type = instance/ip (direto para EKS, perde funcionalidades ALB) |

### Por que Cross-Zone Load Balancing?

| Decisao | Cross-Zone Habilitado |
|---------|----------------------|
| **Motivo** | Distribuir trafego uniformemente entre todas as AZs |
| **Beneficio** | Melhor utilizacao de recursos, alta disponibilidade |
| **Trade-off** | Pequeno custo adicional de transferencia entre AZs |

### Health Check HTTP vs TCP

| Decisao | Health Check HTTP |
|---------|-------------------|
| **Motivo** | Verificar saude real da aplicacao, nao apenas porta aberta |
| **Beneficio** | Detecta problemas na aplicacao, nao apenas infraestrutura |
| **Trade-off** | Requer endpoint de health na aplicacao |

---

## Referencias

### AWS Documentation

- [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/)
- [NLB Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-target-groups.html)
- [NLB com Target Type ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/application-load-balancer-target.html)
- [API Gateway VPC Link](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vpc-links.html)
- [VPC Link para REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-private-integration.html)

### Terraform Documentation

- [aws_lb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb)
- [aws_lb_target_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group)
- [aws_lb_listener](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener)
- [aws_apigatewayv2_vpc_link](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_vpc_link)

### Best Practices

- [Arquitetura API Gateway + VPC Link](https://aws.amazon.com/blogs/compute/introducing-amazon-api-gateway-private-integrations/)
- [NLB Best Practices](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/network-load-balancer-getting-started.html)
- [Cross-Zone Load Balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#cross-zone-load-balancing)

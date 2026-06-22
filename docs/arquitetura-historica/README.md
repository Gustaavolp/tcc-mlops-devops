# Documentação de Arquitetura - ELO Fraud Detection

## Índice de Diagramas

Esta pasta contém a documentação completa da arquitetura do projeto ELO Fraud Detection, incluindo infraestrutura AWS e Kubernetes.

### Diagramas Disponíveis

1. **[Arquitetura AWS Completa](./01-arquitetura-aws-completa.md)**
   - Visão geral de todos os recursos AWS
   - VPC, subnets, e componentes de rede
   - Serviços de computação, armazenamento e ML
   - IAM roles e permissões

2. **[Cluster Kubernetes (EKS)](./02-cluster-kubernetes.md)**
   - Configuração do EKS cluster
   - Deployments, Services, Ingress
   - HPA (Horizontal Pod Autoscaler)
   - Node groups e recursos

3. **[Fluxo de Dados e Comunicação](./03-fluxo-dados-comunicacao.md)**
   - Fluxo de requisição síncrona (Fraud Scoring)
   - Fluxo de processamento assíncrono (Worker)
   - Integração direta API Gateway → SQS
   - Comunicação entre componentes

4. **[Diagrama de Rede](./04-diagrama-rede.md)**
   - Topologia VPC detalhada
   - Subnets públicas e privadas
   - Route tables e VPC endpoints
   - Security groups e conectividade

5. **[Dependências Terraform](./05-dependencias-terraform.md)**
   - Grafo de dependências entre módulos
   - Ordem de deployment
   - Inputs e outputs de cada módulo
   - Critical path de deployment

6. **[Resumo Executivo](./06-resumo-executivo.md)**
   - Custos mensais estimados
   - Pontos de atenção e recomendações
   - Próximos passos
   - Checklist de deployment

---

## Informações Gerais

**Projeto:** ELO Fraud Detection
**Ambiente:** Desenvolvimento (dev)
**AWS Account:** 888577064416
**Região:** us-east-1
**Data da Análise:** 2025-11-23

### Recursos Provisionados

- **Módulos Terraform:** 12
- **Recursos AWS:** 30+
- **Namespaces Kubernetes:** 1 (fraud-detection)
- **Deployments:** 2 (inference, process)
- **Custo Mensal (dev):** ~$210-280 USD

### Tecnologias Utilizadas

- **IaC:** Terraform
- **Container Orchestration:** Amazon EKS (Kubernetes 1.32)
- **Load Balancing:** Application Load Balancer + Ingress
- **ML Platform:** Amazon SageMaker + MLflow
- **Messaging:** Amazon SQS FIFO
- **Storage:** S3, DynamoDB
- **Container Registry:** Amazon ECR

---

## Como Visualizar os Diagramas

Os diagramas estão em formato ASCII art. Para melhor visualização:

1. **No VS Code:** Use a fonte `Courier New` ou `Fira Code`
2. **No PowerPoint:** Cole em caixas de texto com fonte `Consolas` ou `Courier New`
3. **No Terminal:** Use `cat` ou `less` para visualizar

```bash
# Visualizar um diagrama
cat Arquitetura/01-arquitetura-aws-completa.md

# Visualizar todos
for file in Arquitetura/*.md; do echo "=== $file ===" && cat "$file" && echo ""; done
```

---

## Estrutura de Pastas

```
Arquitetura/
├── README.md                           # Este arquivo (índice)
├── 01-arquitetura-aws-completa.md      # Diagrama AWS completo
├── 02-cluster-kubernetes.md            # Diagrama EKS/K8s
├── 03-fluxo-dados-comunicacao.md       # Fluxos de dados
├── 04-diagrama-rede.md                 # Topologia de rede
├── 05-dependencias-terraform.md        # Dependências IaC
└── 06-resumo-executivo.md              # Custos e recomendações
```

---

## Contato e Contribuições

Para dúvidas ou sugestões sobre a arquitetura, contate o time de DevOps.

**Última atualização:** 2025-11-23

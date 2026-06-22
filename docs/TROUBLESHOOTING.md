# Troubleshooting e Monitoramento - Elo Fraud Detection

> **Documento Tecnico para Reuniao E2E**
> **Data**: 2026-01-16
> **Ambiente**: DEV (us-east-1)

---

## 1. Comandos de Diagnostico Rapido

### 1.1 Status Geral do Sistema

```bash
# === VERIFICACAO RAPIDA (executar primeiro) ===

# 1. Pods rodando?
kubectl get pods -n fraud-detection

# 2. Health check OK?
curl -s http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health | jq .

# 3. SQS sem acumulo?
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1 --query 'Attributes.ApproximateNumberOfMessages'

# 4. DLQ vazia?
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1 --query 'Attributes.ApproximateNumberOfMessages'
```

### 1.2 Dashboard de Monitoramento (Terminal)

```bash
#!/bin/bash
# monitor.sh - Dashboard simples no terminal

while true; do
  clear
  echo "=== ELO FRAUD DETECTION - MONITOR ==="
  echo "$(date)"
  echo ""

  echo "--- PODS ---"
  kubectl get pods -n fraud-detection --no-headers 2>/dev/null | \
    awk '{printf "%-30s %-10s %-10s\n", $1, $2, $3}'
  echo ""

  echo "--- HPA ---"
  kubectl get hpa -n fraud-detection --no-headers 2>/dev/null | \
    awk '{printf "%-15s %-25s %-10s\n", $1, $4, $6}'
  echo ""

  echo "--- SQS ---"
  MSGS=$(aws --profile elo sqs get-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
    --attribute-names ApproximateNumberOfMessages --region us-east-1 \
    --query 'Attributes.ApproximateNumberOfMessages' --output text 2>/dev/null)
  echo "Mensagens na fila: $MSGS"

  DLQ=$(aws --profile elo sqs get-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
    --attribute-names ApproximateNumberOfMessages --region us-east-1 \
    --query 'Attributes.ApproximateNumberOfMessages' --output text 2>/dev/null)
  echo "Mensagens na DLQ:  $DLQ"
  echo ""

  echo "--- HEALTH ---"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health)
  echo "Health Check: $HTTP_CODE"

  sleep 10
done
```

---

## 2. Problemas Comuns e Solucoes

### 2.1 Inference Pod

#### Problema: Pod em CrashLoopBackOff

**Sintoma:**
```
NAME                        READY   STATUS             RESTARTS
inference-649b9f7f7-xxxxx   0/1     CrashLoopBackOff   5
```

**Diagnostico:**
```bash
# Ver logs do pod com crash
kubectl logs -n fraud-detection deployment/inference --previous

# Ver eventos
kubectl describe pod -n fraud-detection -l app=inference
```

**Causas Comuns:**
1. **Modelo MLflow nao carregado**: Verificar `MLFLOW_TRACKING_URI`
2. **Falta de memoria**: Verificar limits/requests
3. **Erro de codigo**: Ver stack trace nos logs

**Solucao:**
```bash
# Restart do deployment
kubectl rollout restart deployment/inference -n fraud-detection

# Verificar status
kubectl rollout status deployment/inference -n fraud-detection
```

#### Problema: Health Check Falhando (503)

**Sintoma:**
```bash
curl http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health
# Retorna 503 ou timeout
```

**Diagnostico:**
```bash
# Verificar se pods estao Ready
kubectl get pods -n fraud-detection -l app=inference

# Ver logs recentes
kubectl logs -n fraud-detection deployment/inference --tail=50

# Verificar Ingress
kubectl describe ingress inference-ingress -n fraud-detection
```

**Solucao:**
```bash
# Se modelo nao carregou, verificar MLflow
kubectl exec -n fraud-detection deployment/inference -- env | grep MLFLOW

# Restart forcado
kubectl delete pod -n fraud-detection -l app=inference
```

### 2.2 Process Worker

#### Problema: Mensagens Acumulando na SQS

**Sintoma:**
```bash
aws --profile elo sqs get-queue-attributes ... | grep ApproximateNumberOfMessages
# Retorna numero > 0 crescendo
```

**Diagnostico:**
```bash
# Verificar se process esta rodando
kubectl get pods -n fraud-detection -l app=process

# Ver logs do process
kubectl logs -n fraud-detection deployment/process --tail=50

# Verificar erros
kubectl logs -n fraud-detection deployment/process | grep -i error
```

**Causas Comuns:**
1. **Process pod nao esta rodando**
2. **Erro de conexao com DynamoDB/Firehose**
3. **Mensagens com formato invalido**

**Solucao:**
```bash
# Escalar process temporariamente
kubectl scale deployment/process -n fraud-detection --replicas=2

# Verificar processamento
watch -n 5 "aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1"
```

#### Problema: Mensagens na DLQ

**Sintoma:**
```bash
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1
# Retorna numero > 0
```

**Diagnostico:**
```bash
# Ler mensagens da DLQ (sem deletar)
aws --profile elo sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
  --max-number-of-messages 1 \
  --region us-east-1 \
  --query 'Messages[0].Body' | jq .

# Ver por que falhou
kubectl logs -n fraud-detection deployment/process | grep -i "failed\|error\|exception"
```

**Solucao:**
```bash
# Se mensagem e valida, reprocessar manualmente
# 1. Ler da DLQ
# 2. Corrigir se necessario
# 3. Enviar para fila principal
# 4. Deletar da DLQ
```

### 2.3 ALB/Ingress

#### Problema: 502 Bad Gateway

**Sintoma:**
```bash
curl http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score
# HTTP 502
```

**Diagnostico:**
```bash
# Verificar targets do ALB
aws --profile elo elbv2 describe-target-health \
  --target-group-arn $(aws --profile elo elbv2 describe-target-groups \
    --region us-east-1 \
    --query "TargetGroups[?contains(TargetGroupName,'fraud')].TargetGroupArn" \
    --output text) \
  --region us-east-1

# Verificar Ingress
kubectl describe ingress inference-ingress -n fraud-detection
```

**Causas Comuns:**
1. **Todos os targets unhealthy**
2. **Security group bloqueando**
3. **Pod nao responde no health check**

**Solucao:**
```bash
# Verificar se pods estao rodando
kubectl get pods -n fraud-detection -o wide

# Testar diretamente no pod
kubectl exec -n fraud-detection deployment/inference -- curl -s localhost:8000/health
```

#### Problema: 504 Gateway Timeout

**Sintoma:**
```bash
curl http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score
# HTTP 504 apos ~60s
```

**Diagnostico:**
```bash
# Verificar latencia do pod
kubectl exec -n fraud-detection deployment/inference -- \
  curl -s -w "\nTime: %{time_total}s\n" -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TEST","cardHolderDocument":"123","amount":"100","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}'

# Verificar CPU/memoria
kubectl top pods -n fraud-detection
```

**Causas Comuns:**
1. **Modelo muito lento (cold start)**
2. **DynamoDB throttling**
3. **Pod com CPU maxima**

**Solucao:**
```bash
# Se CPU alta, aumentar recursos ou replicas
kubectl scale deployment/inference -n fraud-detection --replicas=4

# Ou editar resources
kubectl edit deployment/inference -n fraud-detection
```

---

## 3. Logs e Metricas

### 3.1 Ver Logs em Tempo Real

```bash
# Inference - todos os pods
kubectl logs -f -n fraud-detection -l app=inference --all-containers

# Process - todos os pods
kubectl logs -f -n fraud-detection -l app=process --all-containers

# Apenas erros
kubectl logs -n fraud-detection deployment/inference | grep -i "error\|exception\|failed"
```

### 3.2 Exportar Logs para Arquivo

```bash
# Ultimas 1000 linhas
kubectl logs -n fraud-detection deployment/inference --tail=1000 > inference_logs.txt
kubectl logs -n fraud-detection deployment/process --tail=1000 > process_logs.txt
```

### 3.3 Metricas de Pod

```bash
# CPU e memoria atual
kubectl top pods -n fraud-detection

# Historico via HPA
kubectl describe hpa -n fraud-detection
```

### 3.4 Metricas AWS

```bash
# DynamoDB - Consumed Capacity
aws --profile elo cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=elo-fraud-customer-recent-tx-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region us-east-1

# SQS - Messages Sent
aws --profile elo cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesSent \
  --dimensions Name=QueueName,Value=elo-fraud-transactions-dev.fifo \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

---

## 4. Verificacoes Pre-Teste

### 4.1 Checklist de Validacao

```bash
#!/bin/bash
# pre_test_check.sh - Executar antes dos testes E2E

echo "=== CHECKLIST PRE-TESTE E2E ==="
echo ""

# 1. EKS Cluster
echo -n "1. EKS Cluster: "
STATUS=$(aws --profile elo eks describe-cluster --name elo-fraud-cluster-dev --region us-east-1 --query 'cluster.status' --output text 2>/dev/null)
[ "$STATUS" == "ACTIVE" ] && echo "OK ($STATUS)" || echo "FALHOU ($STATUS)"

# 2. Pods Running
echo -n "2. Inference Pods: "
READY=$(kubectl get pods -n fraud-detection -l app=inference --no-headers 2>/dev/null | grep -c "Running")
[ "$READY" -ge 2 ] && echo "OK ($READY running)" || echo "ATENCAO ($READY running, esperado >= 2)"

echo -n "3. Process Pod: "
READY=$(kubectl get pods -n fraud-detection -l app=process --no-headers 2>/dev/null | grep -c "Running")
[ "$READY" -ge 1 ] && echo "OK ($READY running)" || echo "FALHOU ($READY running)"

# 3. Health Check
echo -n "4. Health Check: "
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health)
[ "$HTTP" == "200" ] && echo "OK ($HTTP)" || echo "FALHOU ($HTTP)"

# 4. SQS
echo -n "5. SQS Queue: "
MSGS=$(aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1 \
  --query 'Attributes.ApproximateNumberOfMessages' --output text 2>/dev/null)
[ "$MSGS" == "0" ] && echo "OK (vazia)" || echo "ATENCAO ($MSGS mensagens pendentes)"

# 5. DLQ
echo -n "6. DLQ: "
DLQ=$(aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1 \
  --query 'Attributes.ApproximateNumberOfMessages' --output text 2>/dev/null)
[ "$DLQ" == "0" ] && echo "OK (vazia)" || echo "ATENCAO ($DLQ mensagens na DLQ)"

# 6. DynamoDB
echo -n "7. DynamoDB: "
TABLE=$(aws --profile elo dynamodb describe-table --table-name elo-fraud-customer-recent-tx-dev --region us-east-1 --query 'Table.TableStatus' --output text 2>/dev/null)
[ "$TABLE" == "ACTIVE" ] && echo "OK ($TABLE)" || echo "FALHOU ($TABLE)"

# 7. Firehose
echo -n "8. Firehose (transactions): "
FH1=$(aws --profile elo firehose describe-delivery-stream --delivery-stream-name elo-fraud-transactions-firehose-dev --region us-east-1 --query 'DeliveryStreamDescription.DeliveryStreamStatus' --output text 2>/dev/null)
[ "$FH1" == "ACTIVE" ] && echo "OK ($FH1)" || echo "FALHOU ($FH1)"

echo -n "9. Firehose (inference): "
FH2=$(aws --profile elo firehose describe-delivery-stream --delivery-stream-name elo-fraud-inference-firehose-dev --region us-east-1 --query 'DeliveryStreamDescription.DeliveryStreamStatus' --output text 2>/dev/null)
[ "$FH2" == "ACTIVE" ] && echo "OK ($FH2)" || echo "FALHOU ($FH2)"

echo ""
echo "=== FIM DO CHECKLIST ==="
```

---

## 5. Acoes de Emergencia

### 5.1 Restart de Servicos

```bash
# Restart inference
kubectl rollout restart deployment/inference -n fraud-detection

# Restart process
kubectl rollout restart deployment/process -n fraud-detection

# Verificar status
kubectl rollout status deployment/inference -n fraud-detection
kubectl rollout status deployment/process -n fraud-detection
```

### 5.2 Scale Up Emergencial

```bash
# Escalar inference para maximo
kubectl scale deployment/inference -n fraud-detection --replicas=4

# Escalar process
kubectl scale deployment/process -n fraud-detection --replicas=3

# Verificar
kubectl get pods -n fraud-detection
```

### 5.3 Purge da SQS (CUIDADO!)

```bash
# ATENCAO: Isso deleta TODAS as mensagens da fila
aws --profile elo sqs purge-queue \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --region us-east-1
```

### 5.4 Rollback de Deployment

```bash
# Ver historico
kubectl rollout history deployment/inference -n fraud-detection

# Rollback para versao anterior
kubectl rollout undo deployment/inference -n fraud-detection

# Rollback para versao especifica
kubectl rollout undo deployment/inference -n fraud-detection --to-revision=2
```

---

## 6. Contatos de Emergencia

| Area | Responsavel | Acao |
|------|-------------|------|
| DevOps/Infra | Gustavo Liebl Pereira | Problemas de infraestrutura |
| ML/Data Science | Ana/Vinicios | Problemas com modelo |
| Dados 3DS | Denis | Problemas com payload |

---

## 7. URLs de Referencia

```
# AWS Console
EKS:       https://us-east-1.console.aws.amazon.com/eks/home?region=us-east-1#/clusters/elo-fraud-cluster-dev
SQS:       https://us-east-1.console.aws.amazon.com/sqs/v3/home?region=us-east-1#/queues
DynamoDB:  https://us-east-1.console.aws.amazon.com/dynamodbv2/home?region=us-east-1#table?name=elo-fraud-customer-recent-tx-dev
API GW:    https://us-east-1.console.aws.amazon.com/apigateway/main/apis/oc9dm394cf/resources?region=us-east-1
ALB:       https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#LoadBalancers:
CloudWatch: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1
```

---

*Documento gerado em 2026-01-15*

# Best Model Register - Lambda Function

## 📋 Visão Geral

Lambda function serverless responsável pelo registro automatizado de modelos de Machine Learning no MLflow Model Registry. Esta função é acionada automaticamente sempre que um novo experimento é criado no MLflow, avaliando e registrando modelos que apresentam desempenho superior aos modelos atualmente em produção.

## 🏗️ Arquitetura

### Deployment
- **Serviço AWS:** AWS Lambda
- **Nome da Lambda:** `elo-fraud-register-best-model-{stage}`
- **Método de Deploy:** Container Image via Amazon ECR (Elastic Container Registry)
- **Runtime:** Python 3.12
- **Base Image:** `public.ecr.aws/lambda/python:3.12`

### Trigger
A função é acionada automaticamente por eventos de criação de experimentos no MLflow, integrando-se ao pipeline de MLOps para garantir que apenas os melhores modelos sejam promovidos ao registro.

## 📁 Estrutura do Projeto

```
best-model-register/
├── src/
│   ├── best_model_register.py    # Lógica principal de registro de modelos
│   ├── lambda_handler.py          # Entry point da Lambda
│   ├── envs.py                    # Gerenciamento de variáveis de ambiente
│   ├── utils.py                   # Utilitários e decoradores
│   ├── requirements.txt           # Dependências Python
│   └── Dockerfile                 # Configuração da imagem Docker
└── upload_to_s3.py               # Script auxiliar para upload S3
```

## 🔧 Componentes

### 1. `lambda_handler.py`
Entry point da função Lambda. Instancia a classe `MlflowModelRegistry` e executa o processo de registro.

```python
def lambda_handler(event, context):
    registry = MlflowModelRegistry()
    status = registry.register_best_model()
    return status
```

### 2. `best_model_register.py`
Contém a classe `MlflowModelRegistry` com a lógica principal:

#### Funcionalidades Principais
- **Busca de Experimentos:** Identifica o experimento mais recente com base em tags específicas
- **Seleção do Melhor Run:** Ordena runs por métrica de desempenho configurável
- **Comparação de Métricas:** Compara o modelo candidato com o modelo atualmente registrado
- **Registro Condicional:** Registra apenas modelos com desempenho superior
- **Tratamento de Exceções:** Robustez contra falhas de comunicação com MLflow

#### Fluxo de Execução
1. Busca o experimento mais recente com a tag de produção especificada
2. Identifica o melhor run baseado na métrica configurada
3. Compara a métrica do candidato com o modelo registrado atual
4. Registra o novo modelo se ele superar o desempenho do modelo existente
5. Retorna status code apropriado com mensagem descritiva

### 3. `envs.py`
Gerencia as variáveis de ambiente necessárias para operação da Lambda:

| Variável | Descrição |
|----------|-----------|
| `MODEL_NAME` | Nome do modelo no MLflow Model Registry |
| `METRIC_TO_COMPARE` | Métrica utilizada para comparação (ex: `metrics.roc_auc`) |
| `MLFLOW_TRACKING_URI` | URI do servidor MLflow Tracking |
| `MLFLOW_BEST_MODEL_RUN` | Caminho do artefato do modelo no run |
| `MLFLOW_TARGET_TAG_KEY` | Chave da tag para filtrar experimentos |
| `MLFLOW_TARGET_TAG` | Valor da tag para identificar experimentos de produção |

### 4. `utils.py`
Utilitários auxiliares:

- **`log_errors` Decorator:** Captura e formata exceções com traceback limpo e logging estruturado

### 5. `Dockerfile`
Configuração da imagem Docker:

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY best_model_register.py ${LAMBDA_TASK_ROOT}/
COPY envs.py ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY utils.py ${LAMBDA_TASK_ROOT}/
CMD ["lambda_handler.lambda_handler"]
```

## 📦 Dependências

```
boto3                 # SDK AWS para integração com serviços
python-dotenv         # Gerenciamento de variáveis de ambiente
mlflow==3.4.0        # Client MLflow para tracking e registro
sagemaker-mlflow     # Integração MLflow com SageMaker
```

## 🔄 Fluxo Operacional

```mermaid
graph TD
    A[Novo Experimento MLflow] --> B[Lambda Disparada]
    B --> C[Buscar Último Experimento com a tag "stage: prod"]
    C --> D[Identificar Melhor Run]
    D --> E{Existe Modelo Registrado?}
    E -->|Não| F[Registrar Modelo]
    E -->|Sim| G[Comparar Métricas]
    G -->|Candidato Melhor| F
    G -->|Registrado Melhor| H[Não Registrar]
    F --> I[Retornar Success 200]
    H --> J[Retornar No Action 200]
```

## 📊 Respostas da Lambda

### Sucesso (200)
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Model registered successfully.\"}"
}
```

### Nenhum Modelo Elegível (200)
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"No model is eligible for registration.\"}"
}
```

### Experimento Não Encontrado (404)
```json
{
  "statusCode": 404,
  "body": "{\"message\": \"No prods experiments found.\"}"
}
```

### Erro Interno (500)
```json
{
  "statusCode": 500,
  "body": "{\"message\": \"Error registering model: <detalhes>\"}"
}
```

## ⚙️ Configuração e Deploy

### Pré-requisitos
1. AWS Account com permissões para Lambda e ECR
2. MLflowApp configurado
3. Variáveis de ambiente configuradas na Lambda

### Build e Push da Imagem

```bash
# Build da imagem Docker
docker build -t elo-fraud-register-best-model:latest ./src

# Tag para ECR
docker tag elo-fraud-register-best-model:latest <account-id>.dkr.ecr.<region>.amazonaws.com/elo-fraud-register-best-model:latest

# Push para ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/elo-fraud-register-best-model:latest
```

### Configuração da Lambda
1. Criar função Lambda a partir da imagem ECR
2. Configurar variáveis de ambiente conforme `envs.py`
3. Configurar trigger baseado em eventos MLflow (Analisar onde está sendo armazenado o .pkl dos experimentos)
4. Ajustar timeout e memória conforme necessário

## 🔒 Segurança e Boas Práticas

- **Logging Controlado:** MLflow logs reduzidos para ERROR level para minimizar verbosidade
- **Timeouts Configuráveis:** HTTP request timeout e max retries configurados
- **Error Handling:** Tratamento robusto de exceções com mensagens descritivas
- **Variáveis de Ambiente:** Credenciais e configurações gerenciadas via environment variables

## 🎯 Casos de Uso

1. **Registro Automatizado:** Modelo superior é automaticamente promovido ao registry
2. **Governança de Modelos:** Apenas modelos com métricas superiores são registrados
3. **Auditoria:** Histórico completo de decisões de registro via logs
4. **CI/CD MLOps:** Integração nativa com pipelines de treinamento automatizado

## 📈 Métricas e Monitoramento

A função registra logs estruturados incluindo:
- Timestamp de execução
- Experimento avaliado
- Métricas comparadas
- Decisão de registro
- Erros e exceções com traceback limpo

## 🛠️ Troubleshooting

### Modelo Não Registrado
- Verificar se a métrica do candidato é realmente superior
- Validar tags do experimento (`MLFLOW_TARGET_TAG_KEY` e `MLFLOW_TARGET_TAG`)
- Confirmar URI do MLflow Tracking Server

### Erros de Conexão
- Verificar timeout e retry configurations
- Validar conectividade com MLflow server
- Confirmar IAM roles e permissions

### Experimento Não Encontrado
- Verificar filtro de tags na busca
- Confirmar que experimentos estão sendo criados com tags corretas
- Validar `MLFLOW_TARGET_TAG` configuration

---

**Versão:** 1.0
**Última Atualização:** Janeiro 2026
**Mantenedor:** Elo Cartões - Fraud Detection Team

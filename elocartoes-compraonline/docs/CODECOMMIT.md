# Guia CodeCommit — compra-online-repo

## Configuração Atual

| Item | Valor |
|---|---|
| **Repo** | `compra-online-repo` |
| **URL** | `https://git-codecommit.us-east-1.amazonaws.com/v1/repos/compra-online-repo` |
| **Branch** | `gustaavolp-compasso` |
| **Auth** | AWS credential helper via `--profile elo` (SSO) |
| **Local path** | `/home/gustavoliebl/VSCode/compra-online-repo` |
| **Região do repo** | us-east-1 |
| **Região do deploy** | us-east-2 (definido no buildspec) |
| **Trigger** | EventBridge `compra-online-rule` (us-east-1) detecta push → CodePipeline |

---

## Passo a Passo

### 0. Pré-requisito: Sessão AWS ativa

O credential helper usa `--profile elo`. Se o token expirar (erro `ExpiredTokenException`), renovar:

```bash
aws sso login --profile elo
```

Verificar se está válido:

```bash
aws sts get-caller-identity --profile elo
```

---

### 1. Navegar para o repo

```bash
cd /home/gustavoliebl/VSCode/compra-online-repo
```

---

### 2. Ver estado atual

```bash
# Branch atual e status
git branch
git status

# Últimos commits
git log --oneline -10

# Diferenças nos arquivos modificados
git diff
```

---

### 3. Puxar alterações remotas

```bash
git pull origin gustaavolp-compasso
```

---

### 4. Fazer alterações e commitar

```bash
# Editar arquivos...

# Ver o que mudou
git status
git diff

# Adicionar arquivos específicos
git add buildspec.yaml
git add infra/environments/test/platform/glue.tf

# Ou adicionar tudo
git add -A

# Commitar
git commit -m "feat: descrição da alteração"
```

---

### 5. Push (dispara a pipeline automaticamente)

```bash
git push origin gustaavolp-compasso
```

> **Ao pushar**, o EventBridge `compra-online-rule` em us-east-1 detecta a mudança na branch `gustaavolp-compasso` e dispara o CodePipeline, que executa o CodeBuild com o `buildspec.yaml` (deploy das 6 fases em us-east-2).

---

### 6. Acompanhar a pipeline

```bash
# Listar pipelines
aws codepipeline list-pipelines --profile elo --region us-east-1 --output table

# Ver estado da pipeline
aws codepipeline get-pipeline-state \
  --name <PIPELINE_NAME> \
  --profile elo --region us-east-1 \
  --query 'stageStates[].{Stage:stageName,Status:latestExecution.status}' \
  --output table

# Ver builds recentes
aws codebuild list-builds-for-project \
  --project-name <PROJECT_NAME> \
  --profile elo --region us-east-1 \
  --max-items 5 --output json

# Ver logs do build mais recente
aws codebuild batch-get-builds \
  --ids <BUILD_ID> \
  --profile elo --region us-east-1 \
  --query 'builds[0].{Status:buildStatus,StartTime:startTime,EndTime:endTime,Logs:logs.deepLink}' \
  --output json
```

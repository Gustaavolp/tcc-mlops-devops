# CI/CD — pipelines da plataforma

Sete pipelines do **AWS CodePipeline (V2)**, disparados por regras do **Amazon EventBridge** a cada push na branch configurada do repositório **AWS CodeCommit** (monorepo) e executados pelo **AWS CodeBuild**. Tudo está definido como código:

| Onde | O quê |
|---|---|
| [`infra/cicd/`](../infra/cicd/) | Stack Terraform: CodeCommit, pipelines, projetos CodeBuild, regras EventBridge, IAM, EKS Access Entries e testes (`tests/`). |
| [`pipelines/artifacts.json`](artifacts.json) | Fonte única dos 6 artefatos (contexto do build, testes, tipo de deploy e caminhos observados). |
| [`pipelines/buildspecs/`](buildspecs/) | Buildspecs finos; a lógica fica nos scripts. |
| [`pipelines/scripts/`](scripts/) | Detecção de mudanças, build/teste/push, deploy, smoke test, Terraform. |
| [`pipelines/tests/`](tests/) | Testes dos scripts com dublês de `aws`/`kubectl`/`crane`. |
| `services/*/tests`, `lambdas/*/tests`, `models/sagemaker_training/tests` | Testes unitários (pytest) de cada artefato. |

## Pipelines

```
app-<artefato>  (inference, process, training-image, etl-delta-filter, training-launcher, register-best-model)
  Source ─► Build ───────────────────────────────► DeployDev ─────────► ApproveStaging ─► DeployStaging
            DetectChanges → ruff → docker build    deploy + smoke test   (manual)          promove a MESMA imagem
            → pytest NA imagem → push ECR :<commit>                                        (mesmo digest) + deploy + smoke

infra
  Source ─► Validate ─► PlanDev ─► ApproveDev ─► ApplyDev ─► PlanStaging ─► ApproveStaging ─► ApplyStaging
            fmt, validate (12 stacks), terraform test, testes dos scripts

model-rollout (CodeBuild por região, sem pipeline)
  register-best-model registra nova versão ─► evento elo-fraud.mlops/ModelVersionRegistered
  ─► EventBridge ─► kubectl rollout restart deployment/inference ─► smoke test
```

| Tipo de artefato | "Implantação" | Smoke test |
|---|---|---|
| `eks` (inference, process) | `kubectl apply` dos manifestos de `k8s/<env>/` com a imagem fixada no commit; `rollout status`; **rollback automático** (`rollout undo`) se falhar | `GET /health` via API Gateway + imagem e réplicas prontas do Deployment |
| `lambda` (3 funções) | `update-function-code` + espera da atualização | `GET /health` + função `Active/Successful` com a imagem esperada |
| `training-image` | parâmetro SSM `/elo-fraud/<env>/training-image`, lido pela `training-launcher` | `GET /health` + parâmetro e imagem no ECR |

## Decisões de projeto

- **Monorepo + detecção de mudanças.** O CodeCommit não filtra o gatilho por caminho; todo push dispara todos os pipelines. A primeira ação (`detect_changes.sh`) compara o commit com o último **promovido** do artefato (parâmetro SSM `/elo-fraud/cicd/<artefato>/last-promoted-commit`) e encerra a execução se nenhum caminho observado mudou — sem builds nem aprovações desnecessárias. O commit só é registrado após a promoção para Staging; uma mudança rejeitada na aprovação volta a ser proposta no próximo push.
- **Tag imutável = commit.** Os repositórios ECR usam `IMMUTABLE_WITH_EXCLUSION` (só `latest` é mutável, para o bootstrap). Staging recebe a mesma imagem de DEV, copiada com `crane` e verificada por digest.
- **Testes dentro da imagem.** O pytest roda no container recém-construído: as dependências testadas são exatamente as que vão para produção. Dependências de teste não entram na imagem.
- **Smoke test sem efeito colateral.** Usa `GET /health` (cadeia API Gateway → NLB → pod com modelo carregado). Um POST de scoring geraria uma inferência real que seguiria para a fila e para os dados de treino.
- **Análise estática pragmática.** `ruff.toml` bloqueia só erros que quebram a execução (sintaxe, nomes indefinidos etc.); estilo não impede deploy.
- **Terraform seguro.** Plano salvo, aprovado e aplicado tal como revisado. Se uma stack anterior aplicada na mesma execução mudar o plano de uma stack seguinte, o apply é interrompido (`compare_plans.py`) e o pipeline deve ser executado de novo. Lock files versionados e `-lockfile=readonly` garantem os mesmos providers no plan e no apply. A stack `infra/cicd` é validada e testada, mas **nunca aplicada pelo próprio pipeline**.
- **IAM como código.** As permissões das workloads são roles de EKS Pod Identity com privilégio mínimo (stack `platform`); qualquer mudança passa pelo pipeline de infraestrutura (plano + aprovação). O antigo `buildspecs/iam-policy-setup.yaml` foi removido: ele reatribuía ao role dos nós permissões amplas (`sagemaker:*`, `EC2FullAccess`, `ElasticLoadBalancingFullAccess`) que o Terraform havia migrado para o Pod Identity, gerando drift fora do Terraform.
- **Permissões mínimas.** Uma role por responsabilidade. No Kubernetes, os CodeBuild entram pelo grupo `cicd-deployers`, ligado à Role `cicd-deployer` do namespace (`platform-k8s/rbac-cicd.tf`), que inclui os CRDs `ScaledObject` e `TargetGroupBinding`. Só o Terraform tem cluster admin (necessário para os charts Helm) e `AdministratorAccess`, compensados por aprovação antes de todo apply.

## Implantação inicial (uma vez, por um administrador)

1. **Bootstrap** com estado local e migração para o bucket (ver `infra/bootstrap/backend.tf`).
2. **Stacks dos ambientes** (`foundation` → `mlops` → `platform` → `platform-k8s` → `platform-lambdas`) em DEV e Staging.
3. **Stack de CI/CD:** `cd infra/cicd && terraform init && terraform apply` (cria o repositório CodeCommit se `create_repository = true`).
4. **Push** do repositório para a branch configurada. A partir daí, os pipelines assumem.

Os manifestos em `k8s/` e as Lambdas referenciam `:latest` apenas para essa primeira subida; o primeiro ciclo de cada pipeline passa a fixar a imagem do commit.

## Validação local

```bash
make test-images            # ruff + docker build + pytest na imagem, para os 6 artefatos (A=inference para um)
make test-pipelines              # testes dos scripts (dublês) + terraform test da stack infra/cicd
bash pipelines/scripts/tf_stacks.sh validate   # o mesmo da etapa Validate do pipeline de infraestrutura
```

**Estado da validação:** os 6 artefatos (47 testes), os scripts (16 testes), a stack `infra/cicd` (8 testes) e o `validate` das 12 stacks passam localmente. Os pipelines **não foram executados na AWS**: a conta original do projeto foi desativada. Antes do primeiro uso em uma conta nova, revise os nomes fixos do bucket de estado (`elo-fraud-terraform-state-888577064416-us-east-1`) nos `backend.tf` e confirme a disponibilidade do AWS CodeCommit na conta.

#!/usr/bin/env bash
# Testes dos scripts de CI/CD com dublês de aws/kubectl/crane (sem nuvem).
# Uso: bash pipelines/tests/test_scripts.sh
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="$ROOT/pipelines/scripts"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0; FAIL=0

ok()   { PASS=$((PASS+1)); echo "  ok   - $1"; }
nok()  { FAIL=$((FAIL+1)); echo "  FAIL - $1"; }
check() { if eval "$2"; then ok "$1"; else nok "$1"; fi; }

# ------------------------------------------------------------------ dublês
STUBS="$WORK/bin"; mkdir -p "$STUBS"
export CALLS="$WORK/calls.log"
cat > "$STUBS/aws" <<'EOF'
#!/usr/bin/env bash
echo "aws $*" >> "$CALLS"
case "$1 $2" in
  "ssm get-parameter")
    [ -f "$STUB_SSM_VALUE" ] && cat "$STUB_SSM_VALUE" && exit 0
    echo "ParameterNotFound" >&2; exit 254 ;;
  "lambda get-function") echo "Active Successful ${STUB_LAMBDA_URI:-}" ;;
esac
exit 0
EOF
cat > "$STUBS/kubectl" <<'EOF'
#!/usr/bin/env bash
echo "kubectl $*" >> "$CALLS"
if [ "$1" = "apply" ]; then cp "$3"/*.yaml "$RENDER_COPY"/; fi
if [ "$1 $2" = "rollout status" ] && [ "${STUB_ROLLOUT_FAIL:-0}" = "1" ]; then exit 1; fi
exit 0
EOF
cat > "$STUBS/crane" <<'EOF'
#!/usr/bin/env bash
echo "crane $*" >> "$CALLS"
[ "$1" = "digest" ] && { case "$2" in *dev*) echo sha256:abc ;; *) [ -f "$WORK_COPIED" ] && echo sha256:abc || exit 1 ;; esac; }
[ "$1" = "copy" ] && touch "$WORK_COPIED"
exit 0
EOF
chmod +x "$STUBS"/*
export PATH="$STUBS:$PATH"
export STUB_SSM_VALUE="$WORK/ssm_value" WORK_COPIED="$WORK/copied" RENDER_COPY="$WORK/rendered"
mkdir -p "$RENDER_COPY"

# ------------------------------------------------- repositório git de teste
REPO="$WORK/repo"; mkdir -p "$REPO/services/inference" "$REPO/docs" "$REPO/k8s/dev/inference" "$REPO/pipelines"
cp -r "$SCRIPTS" "$REPO/pipelines/scripts"
cd "$REPO" || exit 1
git init -q && git config user.email t@t && git config user.name t
echo a > services/inference/app.py; echo d > docs/x.md
cat > k8s/dev/inference/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference
spec:
  template:
    spec:
      containers:
      - name: inference
        image: 111.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest
EOF
printf 'apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: cfg\n' > k8s/dev/inference/configmap.yaml
git add -A && git commit -qm base
BASE="$(git rev-parse HEAD)"
reset_calls() { : > "$CALLS"; rm -f "$STUB_SSM_VALUE" "$WORK_COPIED"; rm -f "$RENDER_COPY"/*; }
common_detect=(ARTIFACT=inference "WATCH_PATHS=services/inference k8s/dev/inference" PIPELINE_NAME=p PIPELINE_EXECUTION_ID=e1)

echo "detect_changes.sh"
reset_calls
env "${common_detect[@]}" bash pipelines/scripts/detect_changes.sh >/dev/null 2>&1
check "sem commit registrado: segue (não encerra o pipeline)" "! grep -q stop-pipeline-execution '$CALLS'"

echo d2 > docs/x.md && git commit -qam docs
reset_calls; echo "$BASE" > "$STUB_SSM_VALUE"
env "${common_detect[@]}" bash pipelines/scripts/detect_changes.sh >/dev/null 2>&1
check "mudança fora dos caminhos: encerra a execução" "grep -q 'stop-pipeline-execution --pipeline-name p --pipeline-execution-id e1' '$CALLS'"

echo b > services/inference/app.py && git commit -qam app
reset_calls; echo "$BASE" > "$STUB_SSM_VALUE"
env "${common_detect[@]}" bash pipelines/scripts/detect_changes.sh >/dev/null 2>&1
check "mudança no artefato: segue" "! grep -q stop-pipeline-execution '$CALLS'"

reset_calls; echo "0000000000000000000000000000000000000000" > "$STUB_SSM_VALUE"
env "${common_detect[@]}" bash pipelines/scripts/detect_changes.sh >/dev/null 2>&1
check "commit registrado inexistente (force-push): segue" "! grep -q stop-pipeline-execution '$CALLS'"

echo "deploy.sh (eks)"
HEAD_SHA="$(git rev-parse HEAD)"
eks_env=(ARTIFACT=inference TARGET_ENV=staging DEPLOY_KIND=eks
  TARGET_REPO_URL=222.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-inference-staging
  SOURCE_REPO_URL=111.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev
  EKS_CLUSTER=c K8S_NAMESPACE=fraud-detection K8S_DEPLOYMENT=inference MANIFEST_DIRS=k8s/dev/inference)
reset_calls
env "${eks_env[@]}" bash pipelines/scripts/deploy.sh >/dev/null 2>&1; rc=$?
check "deploy termina com sucesso" "[ $rc -eq 0 ]"
check "promove a imagem de dev para staging (crane copy)" "grep -q 'crane copy 111.*-dev:$HEAD_SHA 222.*-staging:$HEAD_SHA' '$CALLS'"
check "manifesto aplicado com a imagem do commit" "grep -q 'image: 222.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-inference-staging:$HEAD_SHA' '$RENDER_COPY'/inference-deployment.yaml"
check "demais manifestos aplicados sem alteração" "cmp -s k8s/dev/inference/configmap.yaml '$RENDER_COPY'/inference-configmap.yaml"
check "aguarda o rollout" "grep -q 'kubectl rollout status deployment/inference -n fraud-detection' '$CALLS'"

reset_calls
env "${eks_env[@]}" STUB_ROLLOUT_FAIL=1 bash pipelines/scripts/deploy.sh >/dev/null 2>&1; rc=$?
check "rollout com falha: deploy falha" "[ $rc -ne 0 ]"
check "rollout com falha: reverte (rollout undo)" "grep -q 'kubectl rollout undo deployment/inference' '$CALLS'"

echo "deploy.sh (lambda / training-image)"
reset_calls
env ARTIFACT=etl TARGET_ENV=dev DEPLOY_KIND=lambda LAMBDA_FUNCTION=f \
  TARGET_REPO_URL=111.dkr.ecr.us-east-1.amazonaws.com/etl-dev bash pipelines/scripts/deploy.sh >/dev/null 2>&1
check "lambda atualizada com a imagem do commit" "grep -q 'aws lambda update-function-code --function-name f --image-uri 111.dkr.ecr.us-east-1.amazonaws.com/etl-dev:$HEAD_SHA --region us-east-1' '$CALLS'"
check "aguarda a atualização da lambda" "grep -q 'aws lambda wait function-updated-v2' '$CALLS'"

reset_calls
env ARTIFACT=t TARGET_ENV=dev DEPLOY_KIND=training-image TRAINING_IMAGE_PARAM=/x/dev/training-image \
  TARGET_REPO_URL=111.dkr.ecr.us-east-1.amazonaws.com/model-dev bash pipelines/scripts/deploy.sh >/dev/null 2>&1
check "imagem de treino publicada no parâmetro SSM" "grep -q 'aws ssm put-parameter --name /x/dev/training-image --type String --value 111.dkr.ecr.us-east-1.amazonaws.com/model-dev:$HEAD_SHA' '$CALLS'"

echo "compare_plans.py"
mk() { python3 -c "import json,sys;print(json.dumps({'resource_changes':[{'address':a,'change':{'actions':[x]}} for a,x in zip(sys.argv[1::2],sys.argv[2::2])]}))" "$@"; }
mk a.b create c.d no-op > "$WORK/p1.json"; mk a.b create > "$WORK/p2.json"; mk a.b update > "$WORK/p3.json"
python3 "$SCRIPTS/compare_plans.py" "$WORK/p1.json" "$WORK/p2.json" >/dev/null; check "planos equivalentes (no-op ignorado)" "[ $? -eq 0 ]"
python3 "$SCRIPTS/compare_plans.py" "$WORK/p1.json" "$WORK/p3.json" >/dev/null; check "planos divergentes detectados" "[ $? -eq 1 ]"

echo
echo "resultado: $PASS ok, $FAIL falha(s)"
[ "$FAIL" -eq 0 ]

#!/usr/bin/env bash
# Build de um artefato conteinerizado: análise estática -> imagem Docker ->
# testes unitários (pytest) executados DENTRO da imagem -> push no ECR com a
# tag igual ao commit.
#
# Variáveis:
#   ARTIFACT      nome lógico (ex.: inference)
#   CONTEXT_DIR   contexto do docker build (ex.: services/inference)
#   LINT_PATHS    caminhos analisados pelo ruff
#   TEST_DIR      diretório de testes no repositório
#   TEST_WORKDIR  diretório do código dentro da imagem (vira PYTHONPATH)
#   TEST_DEPS     dependências de teste instaladas só no container de teste
#   ECR_REPO_URL  repositório de destino (DEV)       [obrigatório se SKIP_PUSH!=1]
#   IMAGE_TAG     tag da imagem (padrão: commit atual)
#   SKIP_PUSH=1   valida localmente sem publicar
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_env ARTIFACT CONTEXT_DIR LINT_PATHS TEST_DIR TEST_WORKDIR TEST_DEPS

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
IMAGE_TAG="${IMAGE_TAG:-$(current_commit)}"
LOCAL_IMAGE="pipelines/${ARTIFACT}:${IMAGE_TAG}"

log "== [1/4] análise estática (ruff, regras em ruff.toml)"
# shellcheck disable=SC2086
ruff check --config ruff.toml $LINT_PATHS

if [ "${SKIP_PUSH:-0}" != "1" ]; then
  require_env ECR_REPO_URL
  ecr_login "$ECR_REPO_URL"
  repo_name="${ECR_REPO_URL#*/}"
  if aws ecr describe-images --region "$(region_of "$ECR_REPO_URL")" \
       --repository-name "$repo_name" --image-ids imageTag="$IMAGE_TAG" >/dev/null 2>&1; then
    log "imagem ${ECR_REPO_URL}:${IMAGE_TAG} já publicada (re-execução do mesmo commit); nada a fazer"
    exit 0
  fi
fi

log "== [2/4] docker build ($CONTEXT_DIR)"
docker build --pull -t "$LOCAL_IMAGE" \
  --label "org.opencontainers.image.revision=${IMAGE_TAG}" \
  --label "org.opencontainers.image.title=${ARTIFACT}" \
  "$CONTEXT_DIR"

log "== [3/4] testes unitários (pytest) dentro da imagem"
# Credenciais fictícias: os testes não podem acessar a AWS.
docker run --rm --user 0 --entrypoint "" \
  -v "$ROOT/$TEST_DIR:/tmp/tests:ro" \
  -w "$TEST_WORKDIR" \
  -e PYTHONPATH="$TEST_WORKDIR" -e PYTHONDONTWRITEBYTECODE=1 \
  -e AWS_DEFAULT_REGION=us-east-1 -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=testing -e AWS_SECRET_ACCESS_KEY=testing \
  "$LOCAL_IMAGE" \
  sh -c "pip install --quiet --no-cache-dir --disable-pip-version-check ${TEST_DEPS} \
         && python -m pytest -q -p no:cacheprovider /tmp/tests"

if [ "${SKIP_PUSH:-0}" = "1" ]; then
  log "SKIP_PUSH=1: imagem $LOCAL_IMAGE validada e não publicada"
  exit 0
fi

log "== [4/4] push ${ECR_REPO_URL}:${IMAGE_TAG}"
docker tag "$LOCAL_IMAGE" "${ECR_REPO_URL}:${IMAGE_TAG}"
docker push "${ECR_REPO_URL}:${IMAGE_TAG}"
digest="$(aws ecr describe-images --region "$(region_of "$ECR_REPO_URL")" \
  --repository-name "${ECR_REPO_URL#*/}" --image-ids imageTag="$IMAGE_TAG" \
  --query 'imageDetails[0].imageDigest' --output text)"
log "publicado ${ECR_REPO_URL}:${IMAGE_TAG} (${digest})"

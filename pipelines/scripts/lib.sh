#!/usr/bin/env bash
# Funções comuns aos scripts de CI/CD. Uso: source "$(dirname "$0")/lib.sh"

log()  { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
warn() { printf '[%s] AVISO: %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }
die()  { printf '[%s] ERRO: %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; exit 1; }

# require_env VAR1 VAR2 ... -> falha se alguma variável estiver vazia
require_env() {
  local missing=()
  for v in "$@"; do
    [ -n "${!v:-}" ] || missing+=("$v")
  done
  [ ${#missing[@]} -eq 0 ] || die "variáveis obrigatórias ausentes: ${missing[*]}"
}

# Commit em processamento: CodeBuild expõe CODEBUILD_RESOLVED_SOURCE_VERSION;
# fora dele, usa o HEAD do repositório local.
current_commit() {
  if [ -n "${CODEBUILD_RESOLVED_SOURCE_VERSION:-}" ]; then
    echo "$CODEBUILD_RESOLVED_SOURCE_VERSION"
  else
    git rev-parse HEAD
  fi
}

# Nome do parâmetro SSM que guarda o último commit promovido de um artefato
state_param() { echo "${STATE_PARAM_PREFIX:-/elo-fraud/cicd}/$1/last-promoted-commit"; }

# Registry (host) a partir da URL de um repositório ECR
registry_of() { echo "${1%%/*}"; }

# Região a partir da URL de um repositório ECR (<conta>.dkr.ecr.<região>.amazonaws.com/...)
region_of() { echo "$1" | sed -E 's#^[0-9]+\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com/.*#\1#'; }

ecr_login() {
  local repo_url="$1"
  aws ecr get-login-password --region "$(region_of "$repo_url")" \
    | docker login --username AWS --password-stdin "$(registry_of "$repo_url")" >/dev/null
}

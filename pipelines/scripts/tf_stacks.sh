#!/usr/bin/env bash
# Pipeline de infraestrutura (Terraform).
#
#   tf_stacks.sh validate          fmt -check + validate de todas as stacks (sem backend)
#   tf_stacks.sh plan  <dev|staging>   plan de cada stack, na ordem, salvo em $PLAN_DIR
#   tf_stacks.sh apply <dev|staging>   aplica os planos salvos (aprovados), na ordem
#
# Ordem: [bootstrap, apenas em dev] foundation -> mlops -> platform -> platform-k8s
#        -> platform-lambdas. A stack infra/cicd (os próprios pipelines) é validada,
#        mas nunca aplicada pelo pipeline, para evitar que ele altere a si mesmo.
#
# Variáveis: PLAN_DIR (padrão: plans/), PLAN_INPUT_DIR (no apply: artefato do plan).
set -euo pipefail
source "$(dirname "$0")/lib.sh"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
SCRIPTS="$ROOT/pipelines/scripts"
STACKS=(foundation mlops platform platform-k8s platform-lambdas)
TF_FLAGS=(-input=false -no-color)
export TF_IN_AUTOMATION=1

stack_dirs() {  # lista "nome:diretório" na ordem de aplicação
  local env="$1"
  [ "$env" = "dev" ] && echo "bootstrap:infra/bootstrap"
  for s in "${STACKS[@]}"; do echo "$env-$s:infra/environments/$env/$s"; done
}

tf_init() { terraform -chdir="$1" init "${TF_FLAGS[@]}" -lockfile=readonly "${@:2}" >/dev/null; }

cmd_validate() {
  log "terraform fmt -check -recursive infra"
  terraform fmt -check -recursive -diff infra
  local dirs=(infra/bootstrap infra/cicd)
  for env in dev staging; do for s in "${STACKS[@]}"; do dirs+=("infra/environments/$env/$s"); done; done
  for d in "${dirs[@]}"; do
    tf_init "$d" -backend=false
    terraform -chdir="$d" validate -no-color >/dev/null
    log "válido: $d"
  done
  log "terraform test (infra/cicd, provider simulado)"
  terraform -chdir=infra/cicd test -no-color
  log "testes dos scripts de CI/CD"
  bash "$ROOT/pipelines/tests/test_scripts.sh"
}

cmd_plan() {
  local env="$1" plan_dir="${PLAN_DIR:-$ROOT/plans}"
  mkdir -p "$plan_dir"
  : > "$plan_dir/summary.txt"
  while IFS=: read -r name dir; do
    tf_init "$dir"
    set +e
    terraform -chdir="$dir" plan "${TF_FLAGS[@]}" -lock-timeout=5m \
      -detailed-exitcode -out="$plan_dir/$name.tfplan" > "$plan_dir/$name.txt"
    rc=$?
    set -e
    case $rc in
      0) echo "$name: sem alterações" >> "$plan_dir/summary.txt"; rm -f "$plan_dir/$name.tfplan" ;;
      2) terraform -chdir="$dir" show -json "$plan_dir/$name.tfplan" > "$plan_dir/$name.json"
         echo "$name: $(grep -E '^Plan:' "$plan_dir/$name.txt" || echo 'alterações')" >> "$plan_dir/summary.txt" ;;
      *) cat "$plan_dir/$name.txt"; die "plan falhou em $name" ;;
    esac
  done < <(stack_dirs "$env")
  log "resumo do plano ($env):"; cat "$plan_dir/summary.txt"
}

cmd_apply() {
  local env="$1" plan_dir="${PLAN_INPUT_DIR:-${PLAN_DIR:-$ROOT/plans}}"
  [ -f "$plan_dir/summary.txt" ] || die "artefato de plano não encontrado em $plan_dir"
  local applied_any=0
  while IFS=: read -r name dir; do
    tf_init "$dir"
    if [ ! -f "$plan_dir/$name.tfplan" ]; then
      if [ "$applied_any" -eq 1 ]; then
        set +e
        terraform -chdir="$dir" plan "${TF_FLAGS[@]}" -lock-timeout=5m -detailed-exitcode >/dev/null
        rc=$?
        set -e
        [ "$rc" -eq 0 ] || die "$name: passou a ter alterações após aplicar as stacks anteriores; execute o pipeline novamente"
      fi
      log "$name: sem alterações no plano aprovado"; continue
    fi
    if [ "$applied_any" -eq 1 ]; then
      # Uma stack anterior foi aplicada nesta execução e pode ter mudado saídas
      # consumidas via terraform_remote_state. Só aplica se o plano aprovado
      # continuar idêntico ao plano atual.
      terraform -chdir="$dir" plan "${TF_FLAGS[@]}" -lock-timeout=5m -out="$plan_dir/$name.recheck" >/dev/null
      terraform -chdir="$dir" show -json "$plan_dir/$name.recheck" > "$plan_dir/$name.recheck.json"
      python3 "$SCRIPTS/compare_plans.py" "$plan_dir/$name.json" "$plan_dir/$name.recheck.json" \
        || die "$name: o plano mudou após aplicar as stacks anteriores; execute o pipeline novamente para revisar o novo plano"
    fi
    log "aplicando $name"
    terraform -chdir="$dir" apply "${TF_FLAGS[@]}" -lock-timeout=5m "$plan_dir/$name.tfplan"
    applied_any=1
  done < <(stack_dirs "$env")
}

case "${1:-}" in
  validate) cmd_validate ;;
  plan)     [ -n "${2:-}" ] || die "uso: $0 plan <dev|staging>";  cmd_plan "$2" ;;
  apply)    [ -n "${2:-}" ] || die "uso: $0 apply <dev|staging>"; cmd_apply "$2" ;;
  *) die "uso: $0 {validate | plan <env> | apply <env>}" ;;
esac

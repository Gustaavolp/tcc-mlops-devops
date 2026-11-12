#!/usr/bin/env bash
# Decide se o pipeline de um artefato deve prosseguir.
#
# O CodeCommit não permite filtrar o gatilho por caminho: todo push dispara
# todos os pipelines. Este passo compara o commit atual com o último commit
# promovido do artefato (parâmetro SSM) e, se nenhum caminho observado mudou,
# encerra a execução do pipeline (stop-pipeline-execution), evitando builds e
# aprovações manuais desnecessárias.
#
# Variáveis: ARTIFACT, WATCH_PATHS (separados por espaço), PIPELINE_NAME,
#            PIPELINE_EXECUTION_ID; opcional STATE_PARAM_PREFIX, DRY_RUN=1.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_env ARTIFACT WATCH_PATHS

current="$(current_commit)"
param="$(state_param "$ARTIFACT")"
last="$(aws ssm get-parameter --name "$param" --query Parameter.Value --output text 2>/dev/null || true)"

changed=1
reason=""
if [ -z "$last" ] || [ "$last" = "None" ]; then
  reason="nenhum commit promovido registrado em $param"
elif ! git cat-file -e "${last}^{commit}" 2>/dev/null; then
  reason="commit registrado $last não existe no histórico (rebase/force-push)"
else
  # shellcheck disable=SC2086  # WATCH_PATHS é uma lista separada por espaço
  if git diff --quiet "$last" "$current" -- $WATCH_PATHS; then
    changed=0
    reason="sem alterações em [$WATCH_PATHS] entre $last e $current"
  else
    reason="alterações em [$WATCH_PATHS] desde $last:"
    # shellcheck disable=SC2086
    git diff --name-only "$last" "$current" -- $WATCH_PATHS | sed 's/^/  /'
  fi
fi

log "$ARTIFACT: $reason"

if [ "$changed" -eq 0 ]; then
  if [ "${DRY_RUN:-0}" = "1" ]; then
    log "DRY_RUN: o pipeline seria encerrado aqui"
    exit 0
  fi
  require_env PIPELINE_NAME PIPELINE_EXECUTION_ID
  aws codepipeline stop-pipeline-execution \
    --pipeline-name "$PIPELINE_NAME" \
    --pipeline-execution-id "$PIPELINE_EXECUTION_ID" \
    --reason "Sem alterações para $ARTIFACT desde ${last:0:12}" >/dev/null
  log "execução $PIPELINE_EXECUTION_ID encerrada (nada a implantar)"
fi

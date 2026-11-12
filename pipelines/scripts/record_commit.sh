#!/usr/bin/env bash
# Registra o commit atual como último promovido do artefato (usado por detect_changes.sh).
# Variáveis: ARTIFACT; opcional STATE_PARAM_PREFIX.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_env ARTIFACT

commit="$(current_commit)"
aws ssm put-parameter --name "$(state_param "$ARTIFACT")" --type String \
  --value "$commit" --overwrite >/dev/null
log "$ARTIFACT: commit $commit registrado como promovido"

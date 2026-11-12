#!/usr/bin/env bash
# Testes de fumaça após a implantação.
#
# 1) API: GET /health pelo API Gateway (sem chave), que percorre
#    API Gateway -> VPC Link -> NLB -> pod e só responde 200 com o modelo
#    carregado. Não usa POST de scoring de propósito: uma inferência real seria
#    publicada na fila e acabaria nos dados de treinamento.
# 2) Verificação do alvo implantado (imagem efetivamente em uso).
#
# Variáveis: TARGET_ENV, HEALTH_URL, DEPLOY_KIND, TARGET_REPO_URL, IMAGE_TAG
#            + EKS_CLUSTER/K8S_NAMESPACE/K8S_DEPLOYMENT | LAMBDA_FUNCTION | TRAINING_IMAGE_PARAM
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_env TARGET_ENV HEALTH_URL

ATTEMPTS="${SMOKE_ATTEMPTS:-12}"
INTERVAL="${SMOKE_INTERVAL:-10}"

log "smoke [$TARGET_ENV] GET $HEALTH_URL"
ok=0
for i in $(seq 1 "$ATTEMPTS"); do
  body="$(curl -sS --max-time 10 -w '\n%{http_code}' "$HEALTH_URL" || true)"
  code="$(echo "$body" | tail -n1)"
  if [ "$code" = "200" ] && echo "$body" | grep -q '"healthy"'; then
    ok=1; log "API saudável (tentativa $i)"; break
  fi
  warn "tentativa $i/$ATTEMPTS: HTTP ${code:-sem resposta}"
  sleep "$INTERVAL"
done
[ "$ok" -eq 1 ] || die "API não respondeu saudável em $TARGET_ENV"

[ -n "${DEPLOY_KIND:-}" ] || exit 0
require_env TARGET_REPO_URL IMAGE_TAG
EXPECTED="${TARGET_REPO_URL}:${IMAGE_TAG}"
REGION="$(region_of "$TARGET_REPO_URL")"

case "$DEPLOY_KIND" in
  eks)
    require_env K8S_NAMESPACE K8S_DEPLOYMENT
    running="$(kubectl get "deployment/$K8S_DEPLOYMENT" -n "$K8S_NAMESPACE" \
      -o jsonpath='{.spec.template.spec.containers[0].image}')"
    [ "$running" = "$EXPECTED" ] || die "Deployment usa $running, esperado $EXPECTED"
    read -r desired ready < <(kubectl get "deployment/$K8S_DEPLOYMENT" -n "$K8S_NAMESPACE" \
      -o jsonpath='{.spec.replicas} {.status.readyReplicas}')
    [ "${ready:-0}" -ge 1 ] && [ "${ready:-0}" -eq "$desired" ] \
      || die "réplicas prontas ${ready:-0}/$desired"
    log "Deployment $K8S_DEPLOYMENT: $ready/$desired réplicas prontas com $EXPECTED"
    ;;
  lambda)
    require_env LAMBDA_FUNCTION
    read -r state update uri < <(aws lambda get-function --function-name "$LAMBDA_FUNCTION" \
      --region "$REGION" --query '[Configuration.State, Configuration.LastUpdateStatus, Code.ImageUri]' \
      --output text)
    [ "$state" = "Active" ] && [ "$update" = "Successful" ] || die "Lambda em estado $state/$update"
    [ "$uri" = "$EXPECTED" ] || die "Lambda usa $uri, esperado $EXPECTED"
    log "Lambda $LAMBDA_FUNCTION ativa com $EXPECTED"
    ;;
  training-image)
    require_env TRAINING_IMAGE_PARAM
    value="$(aws ssm get-parameter --name "$TRAINING_IMAGE_PARAM" --region "$REGION" \
      --query Parameter.Value --output text)"
    [ "$value" = "$EXPECTED" ] || die "parâmetro aponta $value, esperado $EXPECTED"
    aws ecr describe-images --region "$REGION" --repository-name "${TARGET_REPO_URL#*/}" \
      --image-ids imageTag="$IMAGE_TAG" >/dev/null || die "imagem $EXPECTED inexistente"
    log "training-launcher apontada para $EXPECTED"
    ;;
  *) die "DEPLOY_KIND inválido: $DEPLOY_KIND" ;;
esac

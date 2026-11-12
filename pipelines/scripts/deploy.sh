#!/usr/bin/env bash
# Implanta uma imagem já publicada em um ambiente (dev | staging).
#
# Comuns:  ARTIFACT, TARGET_ENV, DEPLOY_KIND (eks | lambda | training-image),
#          TARGET_REPO_URL (repositório ECR do ambiente), IMAGE_TAG (padrão: commit)
# Promoção: SOURCE_REPO_URL -> se definido, copia antes a MESMA imagem
#          (mesmo digest) do repositório de origem para TARGET_REPO_URL.
# eks:     EKS_CLUSTER, K8S_NAMESPACE, K8S_DEPLOYMENT, MANIFEST_DIRS
# lambda:  LAMBDA_FUNCTION
# training-image: TRAINING_IMAGE_PARAM (parâmetro SSM lido pela training-launcher)
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_env ARTIFACT TARGET_ENV DEPLOY_KIND TARGET_REPO_URL

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
IMAGE_TAG="${IMAGE_TAG:-$(current_commit)}"
REGION="$(region_of "$TARGET_REPO_URL")"
IMAGE="${TARGET_REPO_URL}:${IMAGE_TAG}"

crane_login() {
  aws ecr get-login-password --region "$(region_of "$1")" \
    | crane auth login -u AWS --password-stdin "$(registry_of "$1")" >/dev/null
}

# ---------------------------------------------------------------- promoção
if [ -n "${SOURCE_REPO_URL:-}" ]; then
  src="${SOURCE_REPO_URL}:${IMAGE_TAG}"
  log "promovendo $src -> $IMAGE"
  crane_login "$SOURCE_REPO_URL"
  crane_login "$TARGET_REPO_URL"
  src_digest="$(crane digest "$src")"
  if dst_digest="$(crane digest "$IMAGE" 2>/dev/null)"; then
    [ "$dst_digest" = "$src_digest" ] || die "tag $IMAGE_TAG já existe no destino com outro digest ($dst_digest)"
    log "imagem já promovida anteriormente ($dst_digest)"
  else
    crane copy "$src" "$IMAGE"
    dst_digest="$(crane digest "$IMAGE")"
    [ "$dst_digest" = "$src_digest" ] || die "digest divergente após cópia: $src_digest != $dst_digest"
    log "imagem promovida com o mesmo digest ($dst_digest)"
  fi
fi

# ---------------------------------------------------------------- implantação
case "$DEPLOY_KIND" in
  eks)
    require_env EKS_CLUSTER K8S_NAMESPACE K8S_DEPLOYMENT MANIFEST_DIRS
    aws eks update-kubeconfig --name "$EKS_CLUSTER" --region "$REGION" >/dev/null
    rendered="$(mktemp -d)"
    # shellcheck disable=SC2086
    for dir in $MANIFEST_DIRS; do
      [ -d "$dir" ] || die "diretório de manifestos inexistente: $dir"
      for f in "$dir"/*.yaml; do
        out="$rendered/$(basename "$dir")-$(basename "$f")"
        if grep -q '^kind: Deployment' "$f"; then
          # Os manifestos versionados usam :latest apenas para bootstrap;
          # o pipeline fixa a imagem imutável do commit.
          [ "$(grep -c 'image:' "$f")" -eq 1 ] || die "$f deve conter exatamente uma linha image:"
          sed -E "s#^([[:space:]]*image:[[:space:]]*).*#\1${IMAGE}#" "$f" > "$out"
        else
          cp "$f" "$out"
        fi
      done
    done
    log "aplicando manifestos em $EKS_CLUSTER/$K8S_NAMESPACE: $(find "$rendered" -name "*.yaml" -printf "%f ")"
    kubectl apply -f "$rendered"
    if ! kubectl rollout status "deployment/$K8S_DEPLOYMENT" -n "$K8S_NAMESPACE" --timeout=10m; then
      warn "rollout falhou; revertendo para a revisão anterior"
      kubectl rollout undo "deployment/$K8S_DEPLOYMENT" -n "$K8S_NAMESPACE"
      kubectl rollout status "deployment/$K8S_DEPLOYMENT" -n "$K8S_NAMESPACE" --timeout=10m || true
      die "implantação de $IMAGE falhou e foi revertida"
    fi
    ;;
  lambda)
    require_env LAMBDA_FUNCTION
    aws lambda update-function-code --function-name "$LAMBDA_FUNCTION" \
      --image-uri "$IMAGE" --region "$REGION" >/dev/null
    aws lambda wait function-updated-v2 --function-name "$LAMBDA_FUNCTION" --region "$REGION"
    ;;
  training-image)
    # Não há serviço em execução: a "implantação" passa a apontar a training-launcher
    # para a nova imagem; o próximo Training Job do ciclo de CT já a utiliza.
    require_env TRAINING_IMAGE_PARAM
    aws ssm put-parameter --name "$TRAINING_IMAGE_PARAM" --type String \
      --value "$IMAGE" --overwrite --region "$REGION" >/dev/null
    ;;
  *) die "DEPLOY_KIND inválido: $DEPLOY_KIND" ;;
esac

log "$ARTIFACT implantado em $TARGET_ENV: $IMAGE"

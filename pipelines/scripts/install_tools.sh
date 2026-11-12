#!/usr/bin/env bash
# Instala ferramentas com versão fixada e verificação de SHA-256.
# Uso: install_tools.sh terraform kubectl crane ruff
set -euo pipefail
source "$(dirname "$0")/lib.sh"

TERRAFORM_VERSION="1.14.9"
TERRAFORM_SHA256="2e5cffc20a0b48a67a76268723bd5a10b8666f69b2aa4f04906e206726bedd63"
KUBECTL_VERSION="v1.32.13"   # compatível com EKS 1.32
KUBECTL_SHA256="db2ae479a63f3665d7f704ab18c0d4d4050144237980763221835b7305703c4c"
CRANE_VERSION="v0.22.1"
CRANE_SHA256="0ab7a1d6932a213aed964ce97666c3077fe691c8606413674a8b3e0b9ec4cda0"
RUFF_VERSION="0.17.4"

BIN_DIR="${TOOLS_BIN_DIR:-/usr/local/bin}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

verify() { echo "$2  $1" | sha256sum -c - >/dev/null || die "checksum inválido para $1"; }

for tool in "$@"; do
  case "$tool" in
    terraform)
      curl -fsSLo "$TMP/tf.zip" "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
      verify "$TMP/tf.zip" "$TERRAFORM_SHA256"
      unzip -oq "$TMP/tf.zip" -d "$TMP" && install -m 0755 "$TMP/terraform" "$BIN_DIR/terraform"
      ;;
    kubectl)
      curl -fsSLo "$TMP/kubectl" "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
      verify "$TMP/kubectl" "$KUBECTL_SHA256"
      install -m 0755 "$TMP/kubectl" "$BIN_DIR/kubectl"
      ;;
    crane)
      curl -fsSLo "$TMP/crane.tgz" "https://github.com/google/go-containerregistry/releases/download/${CRANE_VERSION}/go-containerregistry_Linux_x86_64.tar.gz"
      verify "$TMP/crane.tgz" "$CRANE_SHA256"
      tar -xzf "$TMP/crane.tgz" -C "$TMP" crane && install -m 0755 "$TMP/crane" "$BIN_DIR/crane"
      ;;
    ruff)
      python3 -m pip install --quiet "ruff==${RUFF_VERSION}"
      ;;
    *) die "ferramenta desconhecida: $tool" ;;
  esac
  log "instalado: $tool"
done

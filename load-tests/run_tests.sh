#!/bin/bash
# =============================================================================
# Script de Execução de Testes de Carga
# =============================================================================
# Uso: ./run_tests.sh [CENARIO] [--env dev|staging]
#
# Cenarios disponíveis:
#   smoke     - Validacao basica (5 usuarios, 30s)
#   load      - Carga normal (20 usuarios, 2min)
#   target    - Target 100 RPS (50 usuarios, 2min)
#   stress    - Encontrar limite (100 usuarios, 5min)
#   spike     - Pico de carga (200 usuarios, 1min)
#   rampup    - Ramp-up gradual (10->100 usuarios, 5min)
#   singular  - Latencia singular: 100 payloads sequenciais com keep-alive
#   warmup    - Aquece pods antes de testes (50 requests rapidos)
#   payloads  - 100 payloads reais sequenciais (sem keep-alive)
#   keepalive - 100 payloads com keep-alive (simula SDK real)
#   compare   - Compara latencia com e sem keep-alive
#   web       - Interface web interativa
#
# Exemplos:
#   ./run_tests.sh smoke                 # Smoke test em DEV
#   ./run_tests.sh smoke --env staging   # Smoke test em STAGING
#   ./run_tests.sh singular --env staging # Latencia singular em STAGING
#   ./run_tests.sh warmup --env staging  # Aquece pods de STAGING
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretorio do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Usa Python do venv do projeto (evita conflito de namespace com ~/.local)
PYTHON="${PROJECT_DIR}/.venv/bin/python"
LOCUST="$PYTHON -m locust"

# Cria diretorio de relatorios
mkdir -p reports

# Data/hora para nome do relatorio
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# =============================================================================
# Configuracao de Ambientes (fonte unica de verdade)
# =============================================================================
# DEV: us-east-1 | STAGING: sa-east-1
# Atualizado em: 2026-02-18 (via AWS CLI get-rest-apis + get-api-keys)
# =============================================================================
ENVIRONMENT="dev"

HOST_DEV="https://3papa9zzq5.execute-api.us-east-1.amazonaws.com"
HOST_STAGING="https://4x88z39gl4.execute-api.sa-east-1.amazonaws.com"

APIKEY_DEV="IY8EB31x6z69IzAGJqMXb6pIZARnZOSP4vMuvj5W"
APIKEY_STAGING="6QTQjhwTLn9M4GU9uz6m5IqvK2SVqyy8DZ1jlTri"

HOST="$HOST_DEV"
APIKEY="$APIKEY_DEV"

# Parse --env flag
for arg in "$@"; do
    case "$arg" in
        --env=*)
            ENVIRONMENT="${arg#*=}"
            ;;
        --env)
            shift_next=true
            ;;
        *)
            if [ "$shift_next" = true ]; then
                ENVIRONMENT="$arg"
                shift_next=false
            fi
            ;;
    esac
done

if [ "$ENVIRONMENT" = "staging" ]; then
    HOST="$HOST_STAGING"
    APIKEY="$APIKEY_STAGING"
fi

export LOCUST_ENV="$ENVIRONMENT"

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}  Ambiente: ${YELLOW}${ENVIRONMENT^^}${BLUE} (${HOST})${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_locust() {
    if ! $LOCUST --version &> /dev/null; then
        print_error "Locust nao esta instalado no venv!"
        echo ""
        echo "Instale com:"
        echo "  ${PYTHON} -m pip install locust"
        exit 1
    fi
}

check_python() {
    if ! $PYTHON --version &> /dev/null; then
        print_error "Python nao encontrado em: ${PYTHON}"
        exit 1
    fi
}

# =============================================================================
# Health check - valida conectividade antes de rodar testes
# =============================================================================
run_health_check() {
    print_info "Health check: ${HOST}/v1/health"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "x-api-key: ${APIKEY}" \
        "${HOST}/v1/health" 2>&1) || true

    if [ "$status" = "200" ]; then
        print_info "Health check OK (HTTP 200)"
        return 0
    else
        print_error "Health check FALHOU (HTTP ${status})"
        print_error "Verifique: URL, API key, VPC Link, pods"
        return 1
    fi
}

# =============================================================================
# Cenarios Locust (carga distribuida)
# =============================================================================

run_smoke() {
    print_header "SMOKE TEST"
    print_info "Objetivo: Validacao basica da API"
    print_info "Configuracao: 5 usuarios, 30 segundos"
    echo ""
    run_health_check || exit 1
    echo ""

    $LOCUST -f locustfile.py \
        --headless \
        --users 5 \
        --spawn-rate 5 \
        --run-time 30s \
        --host "$HOST" \
        --html "reports/smoke_${ENVIRONMENT}_${TIMESTAMP}.html" \
        --csv "reports/smoke_${ENVIRONMENT}_${TIMESTAMP}"
}

run_load() {
    print_header "LOAD TEST"
    print_info "Objetivo: Carga normal de producao"
    print_info "Configuracao: 20 usuarios, 2 minutos"
    echo ""
    run_health_check || exit 1
    echo ""

    $LOCUST -f locustfile.py \
        --headless \
        --users 20 \
        --spawn-rate 5 \
        --run-time 2m \
        --host "$HOST" \
        --html "reports/load_${ENVIRONMENT}_${TIMESTAMP}.html" \
        --csv "reports/load_${ENVIRONMENT}_${TIMESTAMP}"
}

run_target() {
    print_header "TARGET 100 RPS TEST"
    print_info "Objetivo: Atingir 100 RPS com p95 < 500ms"
    print_info "Configuracao: 50 usuarios, 2 minutos"
    print_info "Formula: usuarios = target_rps * latencia_media_segundos"
    print_info "Com 300ms de latencia: 100 * 0.3 = 30 (usando 50 para margem)"
    echo ""
    run_health_check || exit 1
    echo ""

    $LOCUST -f locustfile.py \
        --headless \
        --users 50 \
        --spawn-rate 10 \
        --run-time 2m \
        --host "$HOST" \
        --html "reports/target100rps_${ENVIRONMENT}_${TIMESTAMP}.html" \
        --csv "reports/target100rps_${ENVIRONMENT}_${TIMESTAMP}"
}

run_stress() {
    print_header "STRESS TEST"
    print_info "Objetivo: Encontrar o limite da infraestrutura"
    print_info "Configuracao: 100 usuarios, 5 minutos"
    print_warn "Este teste pode causar degradacao de performance!"
    echo ""

    read -p "Continuar? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Teste cancelado."
        exit 0
    fi

    run_health_check || exit 1
    echo ""

    $LOCUST -f locustfile.py \
        --headless \
        --users 100 \
        --spawn-rate 20 \
        --run-time 5m \
        --host "$HOST" \
        --html "reports/stress_${ENVIRONMENT}_${TIMESTAMP}.html" \
        --csv "reports/stress_${ENVIRONMENT}_${TIMESTAMP}"
}

run_spike() {
    print_header "SPIKE TEST"
    print_info "Objetivo: Testar resposta a pico subito de carga"
    print_info "Configuracao: 200 usuarios, spawn instantaneo, 1 minuto"
    print_warn "Este teste simula um pico extremo de trafego!"
    echo ""

    read -p "Continuar? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Teste cancelado."
        exit 0
    fi

    run_health_check || exit 1
    echo ""

    $LOCUST -f locustfile.py \
        --headless \
        --users 200 \
        --spawn-rate 100 \
        --run-time 1m \
        --host "$HOST" \
        --html "reports/spike_${ENVIRONMENT}_${TIMESTAMP}.html" \
        --csv "reports/spike_${ENVIRONMENT}_${TIMESTAMP}"
}

run_rampup() {
    print_header "RAMP-UP TEST"
    print_info "Objetivo: Ramp-up gradual de 10 a 100 usuarios"
    print_info "Configuracao: Aumenta 10 usuarios a cada 30s"
    echo ""
    run_health_check || exit 1
    echo ""

    # Ramp-up manual em estagios
    for users in 10 20 30 50 75 100; do
        print_info "Estagio: ${users} usuarios por 30s..."
        $LOCUST -f locustfile.py \
            --headless \
            --users $users \
            --spawn-rate 10 \
            --run-time 30s \
            --host "$HOST" \
            --csv "reports/rampup_${ENVIRONMENT}_${users}u_${TIMESTAMP}" \
            2>&1 | grep -E "(RPS|p95|requests)" || true
        echo ""
    done

    print_info "Ramp-up completo! Relatorios em reports/"
}

run_web() {
    print_header "INTERFACE WEB"
    print_info "Iniciando Locust com interface web..."
    print_info "Acesse: http://localhost:8089"
    print_info "Ctrl+C para parar"
    echo ""

    $LOCUST -f locustfile.py --host "$HOST"
}

# =============================================================================
# Cenarios Python (latencia singular / payloads reais)
# =============================================================================

run_warmup() {
    print_header "WARMUP - Aquecimento de Pods"
    print_info "Envia 50 requests rapidos para aquecer todos os pods"
    print_info "Aquece: conexoes TLS, DynamoDB pool, modelo XGBoost no cache L3"
    echo ""
    run_health_check || exit 1
    echo ""

    $PYTHON test_100_keepalive.py \
        --env "$ENVIRONMENT" \
        --delay 0.02 \
        --output "reports/warmup_${ENVIRONMENT}_${TIMESTAMP}.csv"
}

run_singular() {
    print_header "SINGULAR LATENCY TEST"
    print_info "Objetivo: Medir latencia individual de cada inferencia"
    print_info "Modo: Sequencial com keep-alive (simula SDK real)"
    print_info "100 payloads reais, 50ms entre requests"
    echo ""
    run_health_check || exit 1
    echo ""

    $PYTHON test_100_keepalive.py \
        --env "$ENVIRONMENT" \
        --delay 0.05 \
        --output "reports/singular_${ENVIRONMENT}_${TIMESTAMP}.csv"
}

run_payloads() {
    print_header "100 PAYLOADS TEST (sem keep-alive)"
    print_info "Objetivo: Teste com nova conexao TCP+TLS a cada request"
    print_info "Mede latencia real incluindo handshake TLS"
    echo ""
    run_health_check || exit 1
    echo ""

    $PYTHON test_100_payloads.py \
        --env "$ENVIRONMENT" \
        --delay 0.1 \
        --output "reports/payloads_${ENVIRONMENT}_${TIMESTAMP}.csv"
}

run_keepalive() {
    print_header "100 PAYLOADS TEST (com keep-alive)"
    print_info "Objetivo: Teste com reutilizacao de conexao TCP+TLS"
    print_info "Simula comportamento real de SDKs e clientes HTTP"
    echo ""
    run_health_check || exit 1
    echo ""

    $PYTHON test_100_keepalive.py \
        --env "$ENVIRONMENT" \
        --delay 0.05 \
        --output "reports/keepalive_${ENVIRONMENT}_${TIMESTAMP}.csv"
}

run_compare() {
    print_header "COMPARACAO: keep-alive vs sem keep-alive"
    print_info "Roda ambos os modos e compara latencia"
    echo ""
    run_health_check || exit 1
    echo ""

    $PYTHON test_100_keepalive.py \
        --env "$ENVIRONMENT" \
        --compare \
        --output "reports/compare_${ENVIRONMENT}_${TIMESTAMP}.csv"
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    echo ""
    echo "Uso: $0 [CENARIO] [--env dev|staging]"
    echo ""
    echo "Cenarios Locust (carga distribuida):"
    echo "  smoke     - Validacao basica (5 usuarios, 30s)"
    echo "  load      - Carga normal (20 usuarios, 2min)"
    echo "  target    - Target 100 RPS (50 usuarios, 2min)"
    echo "  stress    - Encontrar limite (100 usuarios, 5min)"
    echo "  spike     - Pico de carga (200 usuarios, 1min)"
    echo "  rampup    - Ramp-up gradual (10->100 usuarios, 5min)"
    echo "  web       - Interface web interativa"
    echo ""
    echo "Cenarios Python (latencia singular):"
    echo "  warmup    - Aquece pods antes de testes (50 requests)"
    echo "  singular  - Latencia individual com keep-alive (100 payloads)"
    echo "  payloads  - 100 payloads sem keep-alive (nova TLS cada request)"
    echo "  keepalive - 100 payloads com keep-alive (reutiliza conexao)"
    echo "  compare   - Compara latencia com e sem keep-alive"
    echo ""
    echo "Ambientes:"
    echo "  --env dev       DEV     us-east-1  (3papa9zzq5) [padrao]"
    echo "  --env staging   STAGING sa-east-1  (4x88z39gl4)"
    echo ""
    echo "Exemplos:"
    echo "  $0 smoke --env staging       # Smoke test em STAGING"
    echo "  $0 warmup --env staging      # Aquece pods de STAGING"
    echo "  $0 singular --env staging    # Latencia singular em STAGING"
    echo "  $0 target --env staging      # 100 RPS em STAGING"
    echo "  $0 web --env staging         # Interface web para STAGING"
    echo ""
    echo "Fluxo recomendado para reuniao:"
    echo "  1. $0 warmup --env staging   # Aquece pods"
    echo "  2. $0 singular --env staging # Mede latencia individual"
    echo "  3. $0 target --env staging   # Testa 100 RPS"
    echo ""
    echo "Relatorios salvos em: load-tests/reports/"
    echo ""
}

# Verifica dependencias
check_python
check_locust

# Main
case "${1:-help}" in
    smoke)
        run_smoke
        ;;
    load)
        run_load
        ;;
    target)
        run_target
        ;;
    stress)
        run_stress
        ;;
    spike)
        run_spike
        ;;
    rampup)
        run_rampup
        ;;
    web)
        run_web
        ;;
    warmup)
        run_warmup
        ;;
    singular)
        run_singular
        ;;
    payloads)
        run_payloads
        ;;
    keepalive)
        run_keepalive
        ;;
    compare)
        run_compare
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Cenario desconhecido: $1"
        show_help
        exit 1
        ;;
esac

echo ""
print_info "Relatorios salvos em: ${SCRIPT_DIR}/reports/"
echo ""

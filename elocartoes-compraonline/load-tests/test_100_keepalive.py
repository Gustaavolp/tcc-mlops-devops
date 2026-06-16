"""
Teste de 100 payloads com reutilização de conexão (HTTP keep-alive).
Simula o comportamento real de clientes como Insomnia, Postman e SDKs.

Comparação:
  - test_100_payloads.py: nova conexão TCP+TLS a cada request (urllib)
  - test_100_keepalive.py: reutiliza conexão via requests.Session (keep-alive)

Uso:
    python test_100_keepalive.py                       # DEV (padrão)
    python test_100_keepalive.py --env staging          # STAGING
    python test_100_keepalive.py --compare              # Roda ambos os modos e compara
"""

import json
import time
import csv
import sys
import argparse
import requests

# --- CONFIGURAÇÃO POR AMBIENTE ---
ENVIRONMENTS = {
    "dev": {
        "base_url": "https://3papa9zzq5.execute-api.us-east-1.amazonaws.com/v1",
        "api_key": "IY8EB31x6z69IzAGJqMXb6pIZARnZOSP4vMuvj5W",
    },
    "staging": {
        "base_url": "https://4x88z39gl4.execute-api.sa-east-1.amazonaws.com/v1",
        "api_key": "6QTQjhwTLn9M4GU9uz6m5IqvK2SVqyy8DZ1jlTri",
    },
}

PAYLOAD_FILE = "../output 1.json"


def run_with_session(payloads, base_url, api_key, delay):
    """Envia payloads reutilizando conexão TCP+TLS (requests.Session)."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "x-api-key": api_key,
    })

    # Warmup: 1 request para estabelecer conexão TLS
    warmup_start = time.perf_counter()
    session.get(f"{base_url}/health", timeout=10)
    warmup_ms = (time.perf_counter() - warmup_start) * 1000
    print(f"  Warmup (TLS handshake): {warmup_ms:.0f}ms\n")

    results = []
    total = len(payloads)

    for i, payload in enumerate(payloads):
        tx_id = payload.get("threeDSServerTransID", f"unknown-{i}")

        start = time.perf_counter()
        try:
            resp = session.post(
                f"{base_url}/authorize-purchase",
                json=payload,
                timeout=30,
            )
            elapsed = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                result = {
                    "index": i + 1,
                    "tx_id": tx_id,
                    "status": 200,
                    "score": data.get("score"),
                    "fraud_label": data.get("fraud_label"),
                    "latency_ms": round(elapsed, 1),
                    "error": None,
                }
            else:
                result = {
                    "index": i + 1,
                    "tx_id": tx_id,
                    "status": resp.status_code,
                    "score": None,
                    "fraud_label": None,
                    "latency_ms": round(elapsed, 1),
                    "error": resp.text[:200],
                }
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            result = {
                "index": i + 1,
                "tx_id": tx_id,
                "status": 0,
                "score": None,
                "fraud_label": None,
                "latency_ms": round(elapsed, 1),
                "error": str(e)[:200],
            }

        results.append(result)

        status_icon = "OK" if result["status"] == 200 else "ERRO"
        print(
            f"  [{result['index']:3d}/{total}] {status_icon} | "
            f"HTTP {result['status']} | "
            f"{result['latency_ms']:7.1f}ms | "
            f"score={result['score']} | "
            f"fraud={result['fraud_label']} | "
            f"tx={result['tx_id'][:16]}..."
        )

        if delay > 0 and i < total - 1:
            time.sleep(delay)

    session.close()
    return results


def run_without_session(payloads, base_url, api_key, delay):
    """Envia payloads SEM reutilizar conexão (nova TCP+TLS a cada request)."""
    results = []
    total = len(payloads)

    for i, payload in enumerate(payloads):
        tx_id = payload.get("threeDSServerTransID", f"unknown-{i}")

        start = time.perf_counter()
        try:
            resp = requests.post(
                f"{base_url}/authorize-purchase",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                },
                timeout=30,
            )
            elapsed = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                result = {
                    "index": i + 1,
                    "tx_id": tx_id,
                    "status": 200,
                    "score": data.get("score"),
                    "fraud_label": data.get("fraud_label"),
                    "latency_ms": round(elapsed, 1),
                    "error": None,
                }
            else:
                result = {
                    "index": i + 1,
                    "tx_id": tx_id,
                    "status": resp.status_code,
                    "score": None,
                    "fraud_label": None,
                    "latency_ms": round(elapsed, 1),
                    "error": resp.text[:200],
                }
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            result = {
                "index": i + 1,
                "tx_id": tx_id,
                "status": 0,
                "score": None,
                "fraud_label": None,
                "latency_ms": round(elapsed, 1),
                "error": str(e)[:200],
            }

        results.append(result)

        status_icon = "OK" if result["status"] == 200 else "ERRO"
        print(
            f"  [{result['index']:3d}/{total}] {status_icon} | "
            f"HTTP {result['status']} | "
            f"{result['latency_ms']:7.1f}ms | "
            f"score={result['score']} | "
            f"fraud={result['fraud_label']} | "
            f"tx={result['tx_id'][:16]}..."
        )

        if delay > 0 and i < total - 1:
            time.sleep(delay)

    return results


def print_stats(results, label):
    """Imprime estatísticas de latência."""
    successes = [r for r in results if r["status"] == 200]
    lats = sorted([r["latency_ms"] for r in successes])
    n = len(lats)
    if n == 0:
        print(f"  {label}: sem resultados")
        return

    p50 = lats[int(n * 0.50)]
    p75 = lats[int(n * 0.75)]
    p90 = lats[int(n * 0.90)]
    p95 = lats[int(n * 0.95)]
    p99 = lats[int(n * 0.99)]
    avg = sum(lats) / n

    print(f"  {label}:")
    print(f"    Sucesso: {n}/{len(results)}")
    print(f"    p50={p50:.0f}ms  p75={p75:.0f}ms  p90={p90:.0f}ms  p95={p95:.0f}ms  p99={p99:.0f}ms")
    print(f"    avg={avg:.0f}ms  min={lats[0]:.0f}ms  max={lats[-1]:.0f}ms")

    sla_ok = sum(1 for l in lats if l < 500)
    print(f"    SLA < 500ms: {sla_ok}/{n} ({sla_ok/n*100:.0f}%)")


def save_csv(results, filename):
    """Salva resultados em CSV."""
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["index", "tx_id", "status", "score", "fraud_label", "latency_ms", "error"],
        )
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in writer.fieldnames})
    print(f"\n  Salvo em: {filename}")


def compare_scores(results_a, results_b, label_a, label_b):
    """Compara scores entre duas execuções."""
    map_a = {r["tx_id"]: r for r in results_a if r["status"] == 200}
    map_b = {r["tx_id"]: r for r in results_b if r["status"] == 200}

    match = 0
    diff = 0
    for tx_id in map_a:
        if tx_id in map_b:
            if str(map_a[tx_id]["score"]) == str(map_b[tx_id]["score"]):
                match += 1
            else:
                diff += 1

    print(f"\n  Comparação de scores ({label_a} vs {label_b}):")
    print(f"    Idênticos (bit-a-bit): {match}/{match + diff}")
    print(f"    Diferentes: {diff}")


def main():
    parser = argparse.ArgumentParser(description="Teste com keep-alive (reutilização de conexão)")
    parser.add_argument("--env", default="dev", choices=ENVIRONMENTS.keys())
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--output", default="resultados_keepalive.csv")
    parser.add_argument("--payload-file", default=PAYLOAD_FILE)
    parser.add_argument("--compare", action="store_true", help="Roda COM e SEM session e compara")
    args = parser.parse_args()

    env_config = ENVIRONMENTS[args.env]
    base_url = env_config["base_url"]
    api_key = env_config["api_key"]

    print(f"Carregando payloads de: {args.payload_file}")
    with open(args.payload_file) as f:
        payloads = json.load(f)
    print(f"  {len(payloads)} payloads carregados")
    print(f"  Ambiente: {args.env}")
    print(f"  Endpoint: {base_url}/authorize-purchase")

    if args.compare:
        # Modo comparação: roda ambos
        print("\n" + "=" * 70)
        print("MODO 1: SEM keep-alive (nova conexão TCP+TLS a cada request)")
        print("=" * 70)
        results_no_session = run_without_session(payloads, base_url, api_key, args.delay)

        print("\n" + "=" * 70)
        print("MODO 2: COM keep-alive (reutiliza conexão TCP+TLS)")
        print("=" * 70)
        results_session = run_with_session(payloads, base_url, api_key, args.delay)

        print("\n" + "=" * 70)
        print("RESULTADO DA COMPARAÇÃO")
        print("=" * 70)
        print_stats(results_no_session, "SEM keep-alive (simula urllib/curl)")
        print()
        print_stats(results_session, "COM keep-alive (simula Insomnia/Postman/SDK)")

        # Calcular ganho
        lats_no = sorted([r["latency_ms"] for r in results_no_session if r["status"] == 200])
        lats_yes = sorted([r["latency_ms"] for r in results_session if r["status"] == 200])
        n = len(lats_no)
        if n > 0 and len(lats_yes) > 0:
            p50_no = lats_no[n // 2]
            p50_yes = lats_yes[len(lats_yes) // 2]
            p95_no = lats_no[int(n * 0.95)]
            p95_yes = lats_yes[int(len(lats_yes) * 0.95)]
            print(f"\n  Ganho com keep-alive:")
            print(f"    p50: {p50_no:.0f}ms -> {p50_yes:.0f}ms (redução de {p50_no - p50_yes:.0f}ms / {(1 - p50_yes/p50_no)*100:.0f}%)")
            print(f"    p95: {p95_no:.0f}ms -> {p95_yes:.0f}ms (redução de {p95_no - p95_yes:.0f}ms / {(1 - p95_yes/p95_no)*100:.0f}%)")

        compare_scores(results_no_session, results_session, "sem keep-alive", "com keep-alive")
        save_csv(results_session, args.output)

    else:
        # Modo normal: só com session
        print("\n" + "=" * 70)
        print("COM keep-alive (reutiliza conexão TCP+TLS)")
        print("=" * 70)
        results = run_with_session(payloads, base_url, api_key, args.delay)

        print("\n" + "=" * 70)
        print("RESULTADO")
        print("=" * 70)
        print_stats(results, f"{args.env.upper()} (keep-alive)")
        save_csv(results, args.output)


if __name__ == "__main__":
    main()

"""
Teste de 100 payloads reais contra o API Gateway.
Envia cada payload EXATAMENTE como está no arquivo, sem alterações.

Uso:
    python test_100_payloads.py                          # DEV (padrão)
    python test_100_payloads.py --env staging             # STAGING
    python test_100_payloads.py --concurrency 5           # 5 requests paralelos
    python test_100_payloads.py --delay 0.5               # 500ms entre requests
    python test_100_payloads.py --output resultados.csv   # Salva CSV
"""

import json
import time
import csv
import sys
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def send_request(index, payload, base_url, api_key):
    """Envia UM payload e retorna resultado."""
    url = f"{base_url}/authorize-purchase"
    tx_id = payload.get("threeDSServerTransID", f"unknown-{index}")
    body = json.dumps(payload, default=str).encode("utf-8")

    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)

    start = time.time()
    try:
        with urlopen(req, timeout=30) as resp:
            elapsed = time.time() - start
            response_body = json.loads(resp.read().decode("utf-8"))
            return {
                "index": index + 1,
                "tx_id": tx_id,
                "status": resp.status,
                "score": response_body.get("score"),
                "fraud_label": response_body.get("fraud_label"),
                "latency_ms": round(elapsed * 1000, 1),
                "error": None,
                "response": response_body,
            }
    except HTTPError as e:
        elapsed = time.time() - start
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return {
            "index": index + 1,
            "tx_id": tx_id,
            "status": e.code,
            "score": None,
            "fraud_label": None,
            "latency_ms": round(elapsed * 1000, 1),
            "error": error_body[:200],
            "response": None,
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "index": index + 1,
            "tx_id": tx_id,
            "status": 0,
            "score": None,
            "fraud_label": None,
            "latency_ms": round(elapsed * 1000, 1),
            "error": str(e)[:200],
            "response": None,
        }


def run_sequential(payloads, base_url, api_key, delay):
    """Envia payloads um a um."""
    results = []
    total = len(payloads)
    for i, payload in enumerate(payloads):
        result = send_request(i, payload, base_url, api_key)
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


def run_concurrent(payloads, base_url, api_key, concurrency):
    """Envia payloads com N threads paralelas."""
    results = []
    total = len(payloads)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(send_request, i, p, base_url, api_key): i
            for i, p in enumerate(payloads)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            status_icon = "OK" if result["status"] == 200 else "ERRO"
            print(
                f"  [{result['index']:3d}/{total}] {status_icon} | "
                f"HTTP {result['status']} | "
                f"{result['latency_ms']:7.1f}ms | "
                f"score={result['score']} | "
                f"fraud={result['fraud_label']}"
            )

    results.sort(key=lambda r: r["index"])
    return results


def print_summary(results, elapsed_total):
    """Imprime resumo dos resultados."""
    total = len(results)
    successes = [r for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    latencies = [r["latency_ms"] for r in successes]

    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    print(f"  Total de payloads:    {total}")
    print(f"  Sucesso (HTTP 200):   {len(successes)}")
    print(f"  Erros:                {len(errors)}")
    print(f"  Tempo total:          {elapsed_total:.1f}s")
    print(f"  Throughput:           {total / elapsed_total:.1f} req/s")

    if latencies:
        latencies.sort()
        print(f"\n  --- Latencia (ms) ---")
        print(f"  Min:     {min(latencies):.1f}")
        print(f"  Max:     {max(latencies):.1f}")
        print(f"  Media:   {sum(latencies) / len(latencies):.1f}")
        print(f"  Mediana: {latencies[len(latencies) // 2]:.1f}")
        p95_idx = int(len(latencies) * 0.95)
        p99_idx = int(len(latencies) * 0.99)
        print(f"  p95:     {latencies[p95_idx]:.1f}")
        print(f"  p99:     {latencies[p99_idx]:.1f}")

        sla_ok = sum(1 for l in latencies if l < 500)
        print(f"\n  SLA p95 < 500ms:  {sla_ok}/{len(latencies)} dentro do SLA ({sla_ok/len(latencies)*100:.1f}%)")

    if successes:
        scores = [r["score"] for r in successes if r["score"] is not None]
        frauds = [r for r in successes if r["fraud_label"] is True]
        legit = [r for r in successes if r["fraud_label"] is False]
        print(f"\n  --- Distribuicao de Fraude ---")
        print(f"  Fraude (True):    {len(frauds)}")
        print(f"  Legitimo (False): {len(legit)}")
        if scores:
            print(f"  Score min:        {min(scores):.4f}")
            print(f"  Score max:        {max(scores):.4f}")
            print(f"  Score medio:      {sum(scores) / len(scores):.4f}")

    if errors:
        print(f"\n  --- Erros ---")
        for r in errors:
            print(f"  [{r['index']}] HTTP {r['status']} - {r['error']}")

    print("=" * 70)


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
    print(f"\nResultados salvos em: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Teste de 100 payloads reais")
    parser.add_argument("--env", default="dev", choices=ENVIRONMENTS.keys(), help="Ambiente (default: dev)")
    parser.add_argument("--concurrency", type=int, default=0, help="Requests paralelos (0 = sequencial)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay entre requests sequenciais em segundos (default: 0.1)")
    parser.add_argument("--output", default="resultados_100.csv", help="Arquivo CSV de saida")
    parser.add_argument("--payload-file", default=PAYLOAD_FILE, help="Arquivo JSON com payloads")
    args = parser.parse_args()

    env_config = ENVIRONMENTS[args.env]
    base_url = env_config["base_url"]
    api_key = env_config["api_key"]

    # 1. Carrega payloads (sem alteracao)
    print(f"Carregando payloads de: {args.payload_file}")
    with open(args.payload_file) as f:
        payloads = json.load(f)
    print(f"  {len(payloads)} payloads carregados")
    print(f"  Ambiente: {args.env}")
    print(f"  Endpoint: {base_url}/authorize-purchase")

    # 2. Health check
    print(f"\nHealth check...")
    try:
        req = Request(f"{base_url}/health")
        with urlopen(req, timeout=10) as resp:
            print(f"  {resp.status} - {resp.read().decode()}")
    except Exception as e:
        print(f"  FALHA: {e}")
        print("  Abortando. Verifique conectividade.")
        sys.exit(1)

    # 3. Executa testes
    mode = f"concorrente ({args.concurrency} threads)" if args.concurrency > 0 else f"sequencial (delay {args.delay}s)"
    print(f"\nIniciando testes ({mode})...\n")

    start_total = time.time()

    if args.concurrency > 0:
        results = run_concurrent(payloads, base_url, api_key, args.concurrency)
    else:
        results = run_sequential(payloads, base_url, api_key, args.delay)

    elapsed_total = time.time() - start_total

    # 4. Resumo
    print_summary(results, elapsed_total)

    # 5. Salva CSV
    save_csv(results, args.output)


if __name__ == "__main__":
    main()

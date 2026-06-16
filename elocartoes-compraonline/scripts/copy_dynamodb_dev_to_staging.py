#!/usr/bin/env python3
"""
Copia todos os items do DynamoDB DEV (us-east-1) para STAGING (sa-east-1).

Tabela: elo-fraud-customer-recent-tx-{env}
Schema: acctID (PK) + threeDSServerTransID (SK)

Usa parallel scan (segments) + batch_write_item com threading.
"""

import boto3
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuracao
SOURCE_TABLE = "elo-fraud-customer-recent-tx-dev"
SOURCE_REGION = "us-east-1"
TARGET_TABLE = "elo-fraud-customer-recent-tx-staging"
TARGET_REGION = "sa-east-1"
TOTAL_SEGMENTS = 8
BATCH_SIZE = 25
MAX_RETRIES = 5
PROFILE = "elo"

# Contadores thread-safe
lock = threading.Lock()
total_written = 0
total_scanned = 0


def batch_write_with_retry(target_client, items):
    """Escreve batch de items com retry para UnprocessedItems."""
    request_items = {
        TARGET_TABLE: [{"PutRequest": {"Item": item}} for item in items]
    }

    for attempt in range(MAX_RETRIES):
        response = target_client.batch_write_item(RequestItems=request_items)
        unprocessed = response.get("UnprocessedItems", {})

        if not unprocessed:
            return len(items)

        request_items = unprocessed
        remaining = sum(len(v) for v in unprocessed.values())
        time.sleep(min(2 ** attempt * 0.1, 5))

    # Retorna quantos foram escritos com sucesso
    failed = sum(len(v) for v in request_items.values())
    return len(items) - failed


def process_segment(segment):
    """Processa um segmento do parallel scan."""
    global total_written, total_scanned

    session = boto3.Session(profile_name=PROFILE)
    source = session.client("dynamodb", region_name=SOURCE_REGION)
    target = session.client("dynamodb", region_name=TARGET_REGION)

    scan_kwargs = {
        "TableName": SOURCE_TABLE,
        "Segment": segment,
        "TotalSegments": TOTAL_SEGMENTS,
    }

    segment_scanned = 0
    segment_written = 0
    batch = []

    while True:
        response = source.scan(**scan_kwargs)
        items = response.get("Items", [])
        segment_scanned += len(items)

        for item in items:
            batch.append(item)
            if len(batch) == BATCH_SIZE:
                written = batch_write_with_retry(target, batch)
                segment_written += written
                batch = []

        # Atualiza contadores globais
        with lock:
            total_scanned += len(items)
            total_written += segment_written
            segment_written = 0
            print(
                f"\r  Progresso: {total_scanned:,} scanned | {total_written:,} written",
                end="",
                flush=True,
            )

        # Proxima pagina
        if "LastEvaluatedKey" not in response:
            break
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    # Flush batch restante
    if batch:
        written = batch_write_with_retry(target, batch)
        with lock:
            total_written += written
            print(
                f"\r  Progresso: {total_scanned:,} scanned | {total_written:,} written",
                end="",
                flush=True,
            )

    return segment_scanned


def main():
    print(f"=== DynamoDB Copy: DEV -> STAGING ===")
    print(f"  Source: {SOURCE_TABLE} ({SOURCE_REGION})")
    print(f"  Target: {TARGET_TABLE} ({TARGET_REGION})")
    print(f"  Segments: {TOTAL_SEGMENTS}")
    print()

    # Verifica se staging esta vazia
    session = boto3.Session(profile_name=PROFILE)
    target = session.client("dynamodb", region_name=TARGET_REGION)
    desc = target.describe_table(TableName=TARGET_TABLE)
    item_count = desc["Table"]["ItemCount"]

    if item_count > 0:
        print(f"  AVISO: Tabela staging tem {item_count:,} items.")
        resp = input("  Continuar e sobrescrever? (s/N): ").strip().lower()
        if resp != "s":
            print("  Abortado.")
            sys.exit(0)

    start = time.time()
    print(f"  Iniciando copia...")

    with ThreadPoolExecutor(max_workers=TOTAL_SEGMENTS) as executor:
        futures = [executor.submit(process_segment, seg) for seg in range(TOTAL_SEGMENTS)]
        for future in as_completed(futures):
            future.result()

    elapsed = time.time() - start
    print()
    print()
    print(f"=== Concluido ===")
    print(f"  Items copiados: {total_written:,}")
    print(f"  Tempo: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Taxa: {total_written/elapsed:.0f} items/s")


if __name__ == "__main__":
    main()

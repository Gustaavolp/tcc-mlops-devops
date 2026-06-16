from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from gerar_base_sintetica import SyntheticPurchaseGenerator, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida payloads sintéticos (ou reais) contra o schema e regras básicas."
    )
    parser.add_argument(
        "--arquivo",
        type=Path,
        required=True,
        help="Arquivo de entrada (JSONL ou CSV) contendo registros para validação.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("configuracoes_cenarios.yaml"),
        help="Configuração utilizada para localizar o schema e parâmetros complementares.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Limita a quantidade de registros lidos do arquivo.",
    )
    parser.add_argument(
        "--max-erros",
        type=int,
        default=25,
        help="Quantidade máxima de mensagens de erro exibidas.",
    )
    return parser.parse_args()


def load_records(path: Path, limit: int | None = None) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    suffix = path.suffix.lower()
    records: List[Dict[str, Any]] = []
    if suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if line.strip():
                    records.append(json.loads(line))
                if limit is not None and len(records) >= limit:
                    break
    elif suffix == ".csv":
        import csv

        with path.open(encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                records.append(dict(row))
                if limit is not None and len(records) >= limit:
                    break
    else:
        raise ValueError(f"Formato de arquivo não suportado: {suffix}")
    return records


def schema_errors(
    generator: SyntheticPurchaseGenerator, records: Sequence[Dict[str, Any]], max_errors: int
) -> List[str]:
    errors: List[str] = []
    for idx, record in enumerate(records):
        for error in generator.validator.iter_errors(record):
            path = "/".join(str(elem) for elem in error.path) or "<root>"
            errors.append(f"[schema] registro {idx} campo {path}: {error.message}")
            if len(errors) >= max_errors:
                return errors
    return errors


def business_rules_errors(
    records: Sequence[Dict[str, Any]], max_errors: int
) -> List[str]:
    errors: List[str] = []
    for idx, record in enumerate(records):
        purchase_currency = record.get("purchaseCurrency")
        recurring_currency = record.get("recurringCurrency")
        if recurring_currency and purchase_currency and recurring_currency != purchase_currency:
            errors.append(
                f"[regra] registro {idx}: recurringCurrency ({recurring_currency}) difere de purchaseCurrency ({purchase_currency})."
            )
        if record.get("payTokenInd") and not record.get("payTokenInfo"):
            errors.append(f"[regra] registro {idx}: payTokenInd=true exige bloco payTokenInfo preenchido.")
        multi = record.get("multiTransaction", {})
        if isinstance(multi, dict) and multi.get("merchantList"):
            try:
                amounts = [int(item.get("merchantAmount", "0")) for item in multi["merchantList"]]
                total = int(record.get("purchaseAmount", "0"))
                if sum(amounts) != total:
                    errors.append(
                        f"[regra] registro {idx}: soma merchantAmount ({sum(amounts)}) difere de purchaseAmount ({total})."
                    )
            except (TypeError, ValueError):
                errors.append(f"[regra] registro {idx}: merchantAmount contém valores não numéricos.")
        if len(errors) >= max_errors:
            break
    return errors


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    generator = SyntheticPurchaseGenerator(config=config, config_path=args.config)
    records = load_records(args.arquivo, args.limite)
    if not records:
        print("Nenhum registro carregado para validação.")
        return
    max_errors = max(1, args.max_erros)
    errors = []
    errors.extend(schema_errors(generator, records, max_errors))
    if len(errors) < max_errors:
        errors.extend(business_rules_errors(records, max_errors - len(errors)))
    if errors:
        print(f"Foram encontrados {len(errors)} erro(s).")
        for msg in errors:
            print(f"- {msg}")
    else:
        print(f"Todos os {len(records)} registro(s) passaram nas validações.")


if __name__ == "__main__":
    main()

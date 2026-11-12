"""Teste ponta a ponta da ETL com uma tabela Delta local (sem S3)."""
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq
import pytest
from deltalake import write_deltalake

import handler

ROWS = [  # data da compra -> conjunto esperado (fim = 2026-04-15 12:00; oot = 1 mês; teste = 1 mês)
    ("2026-01-10 08:00:00", "train"),
    ("2026-02-15 12:00:00", "test"),   # exatamente no início do período de teste
    ("2026-02-20 09:30:00", "test"),
    ("2026-03-15 11:59:59", "test"),   # 1 s antes do início do out-of-time
    ("2026-03-20 18:00:00", "oot"),
    ("2026-04-15 12:00:00", "oot"),    # data máxima da tabela
]


@pytest.fixture
def delta_table(tmp_path, monkeypatch):
    path = tmp_path / "transformed_zone"
    write_deltalake(str(path), pa.table({
        "PURCHASE_DATE_AND_TIME": [d for d, _ in ROWS],
        "dataset_flag": ["antigo"] * len(ROWS),
        "3DS_TRANS_ID": [f"tx-{i}" for i in range(len(ROWS))],
        "CARDHOLDER_ACCOUNT_IDENTIFIER": [f"u-{i}" for i in range(len(ROWS))],
        "AMOUNT": [10.0 * (i + 1) for i in range(len(ROWS))],
        "FLAG_FRAUD": [False, True, False, False, True, False],
    }))
    out = tmp_path / "out"
    (out / "training_zone").mkdir(parents=True)
    # o "S3" de saída vira o sistema de arquivos local
    monkeypatch.setattr(handler.pafs, "S3FileSystem", lambda region=None: pafs.LocalFileSystem())
    return str(path), str(out)


def run(delta_path, out_dir, **kw):
    event = {"delta_table_path": delta_path, "bucket": out_dir, "bucket_folder": "training_zone/", **kw}
    return handler.lambda_handler(event, None)


def test_separa_treino_teste_e_oot_pelas_datas(delta_table):
    result = run(*delta_table)
    assert result["statusCode"] == 200 and result["rows_written"] == len(ROWS)
    assert result["end_date"] == datetime(2026, 4, 15, 12, tzinfo=timezone.utc).isoformat()
    table = pq.read_table(result["output_path"])
    assert table.column("dataset_flag").to_pylist() == [flag for _, flag in ROWS]


def test_remove_identificadores_e_data(delta_table):
    table = pq.read_table(run(*delta_table)["output_path"])
    for col in ("PURCHASE_DATE_AND_TIME", "3DS_TRANS_ID", "CARDHOLDER_ACCOUNT_IDENTIFIER"):
        assert col not in table.column_names
    assert {"AMOUNT", "FLAG_FRAUD", "dataset_flag"} <= set(table.column_names)


def test_janela_de_treino_limita_historico(delta_table):
    result = run(*delta_table, n_months_training=1)   # treino a partir de 2026-01-15 12:00
    flags = pq.read_table(result["output_path"]).column("dataset_flag").to_pylist()
    assert result["rows_written"] == len(ROWS) - 1 and "train" not in flags

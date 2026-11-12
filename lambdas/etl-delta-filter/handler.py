import os
from deltalake import DeltaTable
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds
import pyarrow.compute as pc
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import pyarrow.fs as pafs



# ---------------------------
# Configurações fixas
# ---------------------------
BATCH_SIZE = 20_000

SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET")
TARGET_BUCKET = os.environ.get("TARGET_BUCKET")

COLUMNS_TO_DROP = [
    "PURCHASE_DATE_AND_TIME",
    "dataset_flag",
    "3DS_TRANS_ID",
    "CARDHOLDER_ACCOUNT_IDENTIFIER"
]

# ---------------------------
# Lambda handler
# ---------------------------
def lambda_handler(event, context):
    # ---------------------------
    # Parâmetros
    # ---------------------------
    delta_table_path = event.get("delta_table_path", f"s3://{SOURCE_BUCKET}/transformed_zone/")
    date_column = event.get("date_column", "PURCHASE_DATE_AND_TIME")

    bucket = event.get("bucket", TARGET_BUCKET)
    bucket_folder = event.get("bucket_folder", "training_zone/")

    n_months_oot = event.get("n_months_oot", 1)
    n_months_test = event.get("n_months_test", 1)
    n_months_training = event.get("n_months_training", 0)
    aws_region = event.get("aws_region", "us-east-1")



    # ---------------------------
    # Carrega DeltaTable
    # ---------------------------
    dt = DeltaTable(
        delta_table_path,
        storage_options={"AWS_REGION": "us-east-1"}
    )

    dataset = dt.to_pyarrow_dataset()

    # Descobre a data máxima presente no Delta
    date_only_scanner = dataset.scanner(
        columns=[date_column],
        batch_size=BATCH_SIZE
    )

    max_dt = None

    for batch in date_only_scanner.to_batches():
        table = pa.Table.from_batches([batch])
        dt_col = table[date_column].combine_chunks()

        dt_col = pc.replace_substring_regex(
            dt_col,
            pattern="[-: ]",
            replacement=""
        )

        dt_col = pc.strptime(
            dt_col,
            format="%Y%m%d%H%M%S",
            unit="us"
        ).cast(pa.timestamp("us", tz="UTC"))

        batch_max = pc.max(dt_col).as_py()

        if batch_max and (max_dt is None or batch_max > max_dt):
            max_dt = batch_max


    # Datas de corte
    #end_date = datetime.now(timezone.utc)
    end_date = max_dt
    oot_start = end_date - relativedelta(months=n_months_oot)
    test_start = oot_start - relativedelta(months=n_months_test)

    if n_months_training > 0:
        training_start = test_start - relativedelta(months=n_months_training)
    else:
        training_start = None

    scanner = dataset.scanner(
        batch_size=BATCH_SIZE
    )

    # ---------------------------
    # S3 Writer
    # ---------------------------
    s3_fs = pafs.S3FileSystem(region=aws_region)
    key = (
        f"{bucket_folder}"
        f"transactions_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.parquet"
    )
    output_file = f"{bucket}/{key}"

    writer = None
    rows_written = 0

    # ---------------------------
    # Processamento em batches
    # ---------------------------
    for batch in scanner.to_batches():
        table = pa.Table.from_batches([batch])

        dt_col = table[date_column].combine_chunks()

        dt_col = pc.replace_substring_regex(
            dt_col,
            pattern="[-: ]",
            replacement=""
        )

        dt_col = pc.strptime(
            dt_col,
            format="%Y%m%d%H%M%S",
            unit="us"
        ).cast(pa.timestamp("us", tz="UTC"))

        if n_months_training > 0:
            valid_mask = pc.greater_equal(
                dt_col,
                pa.scalar(training_start, type=dt_col.type)
            )
            table = table.filter(valid_mask)
            # Filtra também a coluna de datas já convertida para timestamp.
            # (Reler table[date_column] devolvia a coluna original em texto e
            # quebrava as comparações seguintes com ArrowTypeError.)
            dt_col = dt_col.filter(valid_mask)

        # Se depois do filtro não sobrar nada, pula o batch
        if table.num_rows == 0:
            continue

        table = table.drop(COLUMNS_TO_DROP)

        # Flags booleanas
        is_oot = pc.greater_equal(dt_col, pa.scalar(oot_start, type=dt_col.type))

        is_test = pc.and_(
            pc.greater_equal(dt_col, pa.scalar(test_start, type=dt_col.type)),
            pc.less(dt_col, pa.scalar(oot_start, type=dt_col.type))
        )

        if n_months_training > 0:
            is_train = pc.and_(
                pc.greater_equal(dt_col, pa.scalar(training_start, type=dt_col.type)),
                pc.less(dt_col, pa.scalar(test_start, type=dt_col.type))
            )
        else:
            is_train = pc.less(
                dt_col, pa.scalar(test_start, type=dt_col.type)
            )

        # Cria coluna dataset_flag
        dataset_flag = pc.if_else(
            is_oot,
            pa.scalar("oot", type=pa.string()),
            pc.if_else(
                is_test,
                pa.scalar("test", type=pa.string()),
                pa.scalar("train", type=pa.string())
            )
        )

        table = table.append_column("dataset_flag", dataset_flag)

        # Cria writer se ainda não existir
        if writer is None:
            base_schema = table.schema
            writer = pq.ParquetWriter(
                output_file,
                base_schema,
                filesystem=s3_fs,
                compression="snappy"
            )
        else:
            table = table.cast(base_schema)

        writer.write_table(table)
        rows_written += table.num_rows

    if writer:
        writer.close()

    if rows_written == 0:
        return {"statusCode": 204, "message": "Nenhum dado encontrado."}

    return {
        "statusCode": 200,
        "rows_written": rows_written,
        "output_path": output_file,
        "oot_start": oot_start.isoformat(),
        "test_start": test_start.isoformat(),
        "end_date": end_date.isoformat()
    }


if __name__ == "__main__":
    print(lambda_handler({}, None))

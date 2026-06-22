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
DELTA_TABLE_PATH = "s3://elo-fraud-data-processed-dev-888577064416/transformed_zone/"
S3_OUTPUT_PATH = "s3://elo-fraud-data-processed-dev-888577064416/training_zone/"
DATE_COLUMN = "dt_transaction_datetime"
BATCH_SIZE = 20_000

COLUMNS_TO_DROP = [
    "enr_user_id",
    "dt_transaction_datetime",
    "nm_merchant_id",
    "dataset_flag"
]

# ---------------------------
# Lambda handler
# ---------------------------
def lambda_handler(event, context):
    # ---------------------------
    # Parâmetros
    # ---------------------------
    n_months_oot = event.get("n_months_oot", 3)
    n_months_test = event.get("n_months_test", 1)
    aws_region = event.get("aws_region", "us-east-1")

    # Datas de corte
    end_date = datetime.now(timezone.utc)
    oot_start = end_date - relativedelta(months=n_months_oot)
    test_start = oot_start - relativedelta(months=n_months_test)



    # ---------------------------
    # Carrega DeltaTable
    # ---------------------------
    dt = DeltaTable(
        DELTA_TABLE_PATH,
        storage_options={"AWS_REGION": "us-east-1"}
    )

    dataset = dt.to_pyarrow_dataset()

    scanner = dataset.scanner(
        batch_size=BATCH_SIZE
    )

    # ---------------------------
    # S3 Writer
    # ---------------------------
    s3_fs = pafs.S3FileSystem(region=aws_region)
    bucket = "elo-fraud-data-processed-dev-888577064416"
    key = (
        "training_zone/"
        f"transactions_"
        f"{end_date.strftime('%Y%m%d%H%M%S')}.parquet"
    )
    output_file = f"{bucket}/{key}"

    writer = None
    rows_written = 0

    # ---------------------------
    # Processamento em batches
    # ---------------------------
    for batch in scanner.to_batches():
        table = pa.Table.from_batches([batch])

        dt_col = table[DATE_COLUMN].combine_chunks()

        table = table.drop(COLUMNS_TO_DROP)
        
        # Flags booleanas
        is_oot = pc.greater_equal(dt_col, pa.scalar(oot_start, type=dt_col.type))
        is_test = pc.and_(
            pc.greater_equal(dt_col, pa.scalar(test_start, type=dt_col.type)),
            pc.less(dt_col, pa.scalar(oot_start, type=dt_col.type))
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
 
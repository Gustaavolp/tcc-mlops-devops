import boto3
import json
from botocore.exceptions import ClientError


class S3BucketUtils:
    def __init__(self, bucket_name, region="us-east-1"):
        self.s3 = boto3.client("s3", region_name=region)
        self.bucket = bucket_name

    # UPLOAD
    def upload_file(self, key, content, content_type="application/json"):
        try:
            if isinstance(content, dict):
                content = json.dumps(content)

            response = self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=content_type
            )
            print(f"UPLOAD OK: {key}")
            return response
        except ClientError as e:
            print("Erro no UPLOAD:", e.response["Error"]["Message"])
            return None

    # READ
    def read_file(self, key, as_json=False):
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            data = response["Body"].read().decode("utf-8")

            print(f"READ OK: {key}")

            if as_json:
                return json.loads(data)

            return data

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                print(f"Arquivo não existe: {key}")
            else:
                print("Erro no READ:", e.response["Error"]["Message"])
            return None
import json
import boto3
import urllib.parse
import urllib.request
import http.cookiejar

sm = boto3.client("sagemaker", region_name="us-east-1")
auth_url = sm.create_presigned_mlflow_app_url(
    Arn="arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ",
    SessionExpirationDurationInSeconds=3600,
)["AuthorizedUrl"]

parsed = urllib.parse.urlparse(auth_url)
base = f"{parsed.scheme}://{parsed.netloc}"

# Abre sessao (cookie) via /auth
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(auth_url).read()

payload = {"filter": "tags.stage = 'prod'", "max_results": 5}
req = urllib.request.Request(
    f"{base}/api/2.0/mlflow/experiments/search",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

resp = opener.open(req)
print(resp.status)
print(resp.read().decode("utf-8")[:500])
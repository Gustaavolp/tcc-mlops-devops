import json
import logging
import os
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any, Dict, List, Optional, Tuple

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_MLFLOW_APP_ARN = os.getenv(
    "MLFLOW_APP_ARN",
    "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ",
)
MLFLOW_APP_REGION = os.getenv(
    "MLFLOW_APP_REGION",
    os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
)
SESSION_EXPIRATION_SECONDS = int(os.getenv("MLFLOW_SESSION_EXPIRATION_SECONDS", "3600"))


def _tags_list_to_dict(tags: List[Dict[str, Any]]) -> Dict[str, str]:
    return {t.get("key"): t.get("value") for t in tags or [] if t.get("key")}


def _list_to_dict(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {i.get("key"): i.get("value") for i in items or [] if i.get("key")}


def _normalize_experiment(exp: Dict[str, Any]) -> Dict[str, Any]:
    exp = dict(exp or {})
    exp["tags"] = _tags_list_to_dict(exp.get("tags", []))
    exp_id = exp.get("experiment_id")
    exp["experiment_id"] = str(exp_id) if exp_id is not None else None
    creation = exp.get("creation_time") or 0
    update = exp.get("last_update_time") or 0
    exp["effective_update_time"] = max(creation, update)
    return exp


def _normalize_run(run: Dict[str, Any]) -> Dict[str, Any]:
    run = dict(run or {})
    info = run.get("info", {})
    data = run.get("data", {})
    return {
        "run_id": info.get("run_id"),
        "experiment_id": str(info.get("experiment_id")) if info.get("experiment_id") is not None else None,
        "status": info.get("status"),
        "start_time": info.get("start_time"),
        "end_time": info.get("end_time"),
        "metrics": _list_to_dict(data.get("metrics", [])),
        "params": _list_to_dict(data.get("params", [])),
        "tags": _list_to_dict(data.get("tags", [])),
    }


def _create_mlflow_session(
    app_arn: str, region: str, expiration_seconds: int
) -> Tuple[str, urllib.request.OpenerDirector]:
    sm = boto3.client("sagemaker", region_name=region)
    resp = sm.create_presigned_mlflow_app_url(
        Arn=app_arn,
        SessionExpirationDurationInSeconds=expiration_seconds,
    )
    auth_url = resp["AuthorizedUrl"]
    parsed = urllib.parse.urlparse(auth_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.open(auth_url).read()
    return base_url, opener


class MlflowAppClient:
    def __init__(
        self,
        app_arn: Optional[str] = None,
        region: Optional[str] = None,
        expiration_seconds: Optional[int] = None,
    ) -> None:
        self.app_arn = app_arn or DEFAULT_MLFLOW_APP_ARN
        self.region = region or MLFLOW_APP_REGION
        self.expiration_seconds = expiration_seconds or SESSION_EXPIRATION_SECONDS
        self.base_url, self._opener = _create_mlflow_session(
            self.app_arn, self.region, self.expiration_seconds
        )

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        with self._opener.open(req) as resp:
            data = resp.read().decode("utf-8")
        return json.loads(data)

    def search_experiments(
        self, filter_string: Optional[str] = None, max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"max_results": max_results}
        if filter_string:
            payload["filter"] = filter_string
        resp = self._post("/api/2.0/mlflow/experiments/search", payload)
        return resp.get("experiments", [])

    def search_runs(
        self,
        experiment_ids: List[str],
        filter_string: Optional[str] = None,
        order_by: Optional[List[str]] = None,
        max_results: int = 1,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "experiment_ids": [str(eid) for eid in experiment_ids],
            "max_results": max_results,
        }
        if filter_string:
            payload["filter"] = filter_string
        if order_by:
            payload["order_by"] = order_by
        resp = self._post("/api/2.0/mlflow/runs/search", payload)
        return resp.get("runs", [])


def is_debug_name(name: Optional[str]) -> bool:
    if not name:
        return False
    return "debug" in name.lower()


def get_latest_run_for_experiment(
    client: MlflowAppClient, experiment_id: str
) -> Optional[Dict[str, Any]]:
    runs = client.search_runs(
        [experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    if not runs:
        runs = client.search_runs(
            [experiment_id],
            order_by=["attributes.start_time DESC"],
            max_results=1,
        )
    if not runs:
        return None
    return _normalize_run(runs[0])


def get_latest_production_run(exclude_debug: bool = True) -> Dict[str, Any]:
    client = MlflowAppClient()
    experiments = client.search_experiments(filter_string="tags.stage = 'prod'")
    normalized = [_normalize_experiment(e) for e in experiments]
    if exclude_debug:
        normalized = [e for e in normalized if not is_debug_name(e.get("name"))]
    if not normalized:
        return {"experiment": None, "run": None}
    latest_exp = max(normalized, key=lambda e: e.get("effective_update_time") or 0)
    latest_run = get_latest_run_for_experiment(client, latest_exp.get("experiment_id"))
    return {"experiment": latest_exp, "run": latest_run}

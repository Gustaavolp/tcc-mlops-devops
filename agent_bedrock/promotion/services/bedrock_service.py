import json
import logging
import os
from typing import Any, Dict, Optional

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0")
AWS_REGION = os.getenv(
    "BEDROCK_REGION",
    os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
)
DEFAULT_MAX_GEN_LEN = int(os.getenv("BEDROCK_MAX_GEN_LEN", "900"))
DEFAULT_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.2"))
DEFAULT_TOP_P = float(os.getenv("BEDROCK_TOP_P", "0.9"))


def get_configured_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)


def _build_llama_prompt(system_text: str, user_text: str) -> str:
    return (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n"
        f"{system_text}\n"
        "<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n"
        f"{user_text}\n"
        "<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n"
    )


def _build_openai_messages(system_text: str, user_text: str) -> list:
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = _sanitize_bedrock_text(text)
    candidates = [cleaned]
    candidate = _extract_first_json_object(cleaned)
    if candidate:
        candidates.append(candidate)

    for candidate in candidates:
        for variant in _build_parse_variants(candidate):
            parsed = _try_parse_json(variant)
            if parsed is not None:
                return parsed
    return None


def _sanitize_bedrock_text(text: str) -> str:
    cleaned = text.strip()
    if "<reasoning>" in cleaned and "</reasoning>" in cleaned:
        cleaned = cleaned.split("</reasoning>", 1)[1].strip()
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned


def _try_parse_json(candidate: str) -> Optional[Dict[str, Any]]:
    for strict in (True, False):
        try:
            return json.loads(candidate, strict=strict)
        except json.JSONDecodeError:
            continue
    return None


def _extract_first_json_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return None


def _build_parse_variants(candidate: str) -> list:
    variants = [candidate]
    repaired = _repair_json_candidate(candidate)
    if repaired != candidate:
        variants.append(repaired)
    closed = _close_open_structures(repaired)
    if closed not in variants:
        variants.append(closed)
    return variants


def _repair_json_candidate(text: str) -> str:
    result = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                if ch == "u":
                    hex_part = text[i + 1 : i + 5]
                    if len(hex_part) == 4 and all(c in "0123456789abcdefABCDEF" for c in hex_part):
                        result.append(ch)
                        result.append(hex_part)
                        i += 5
                        escape = False
                        continue
                    result.append("\\")
                    result.append(ch)
                    i += 1
                    escape = False
                    continue
                if ch in '"\\/bfnrt':
                    result.append(ch)
                    i += 1
                    escape = False
                    continue
                result.append("\\")
                result.append(ch)
                i += 1
                escape = False
                continue
            if ch == "\\":
                result.append(ch)
                escape = True
                i += 1
                continue
            if ch == '"':
                in_string = False
                result.append(ch)
                i += 1
                continue
            if ch == "\n":
                result.append("\\n")
                i += 1
                continue
            if ch == "\r":
                result.append("\\r")
                i += 1
                continue
            if ch == "\t":
                result.append("\\t")
                i += 1
                continue
            result.append(ch)
            i += 1
            continue
        else:
            if ch == '"':
                in_string = True
            result.append(ch)
            i += 1

    if escape:
        result.append("\\")
    return "".join(result)


def _close_open_structures(text: str) -> str:
    depth = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(depth - 1, 0)
    result = text
    if in_string:
        result += '"'
    if depth > 0:
        result += "}" * depth
    return result


def _format_decimal_pt(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def _format_metric_value(value: Optional[float]) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if -1.0 <= numeric <= 1.0:
        return f"{_format_decimal_pt(numeric * 100, 2)}%"
    return _format_decimal_pt(numeric, 4)


def _format_delta_pp(value: Optional[float]) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if -1.0 <= numeric <= 1.0:
        return f"{_format_decimal_pt(numeric * 100, 2)} p.p."
    return _format_decimal_pt(numeric, 4)


def _extract_text_from_content(content: Any) -> Optional[str]:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text = content.get("text")
        if text:
            return text
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
        if parts:
            return "".join(parts)
    return None


def _extract_text_from_response(data: Any) -> str:
    if isinstance(data, dict):
        if data.get("generation"):
            return data.get("generation")
        if data.get("output_text"):
            return data.get("output_text")
        content_text = _extract_text_from_content(data.get("content"))
        if content_text:
            return content_text
        if isinstance(data.get("output"), str):
            return data.get("output")
        if isinstance(data.get("output"), list):
            for item in data.get("output"):
                item_text = _extract_text_from_content(item)
                if item_text:
                    return item_text
        if isinstance(data.get("output"), dict):
            output_text = data["output"].get("text")
            if output_text:
                return output_text
            output_text = _extract_text_from_content(data["output"].get("content"))
            if output_text:
                return output_text
        outputs = data.get("outputs")
        if isinstance(outputs, list):
            for item in outputs:
                item_text = _extract_text_from_content(item)
                if item_text:
                    return item_text
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            choice = choices[0]
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict) and message.get("content"):
                    message_text = _extract_text_from_content(message.get("content"))
                    if message_text:
                        return message_text
                if choice.get("text"):
                    return choice.get("text")
    return ""


def _invoke_model(payload: Dict[str, Any], model_id: str) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    logger.info("Invoking Bedrock model_id=%s region=%s", model_id, AWS_REGION)
    resp = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )
    raw = resp.get("body").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8", errors="ignore")
    return _extract_text_from_response(data)


def _invoke_llama(prompt: str, model_id: str) -> str:
    payload = {
        "prompt": prompt,
        "max_gen_len": DEFAULT_MAX_GEN_LEN,
        "temperature": DEFAULT_TEMPERATURE,
        "top_p": DEFAULT_TOP_P,
    }
    return _invoke_model(payload, model_id)


def _invoke_openai(messages: list, model_id: str) -> str:
    payload = {
        "messages": messages,
        "max_tokens": DEFAULT_MAX_GEN_LEN,
        "temperature": DEFAULT_TEMPERATURE,
        "top_p": DEFAULT_TOP_P,
    }
    return _invoke_model(payload, model_id)


def _is_openai_model(model_id: str) -> bool:
    return model_id.startswith("openai.")


def _build_fallback_email(promotion_data: Dict[str, Any], reason: Optional[str]) -> Dict[str, Any]:
    model_name = promotion_data.get("model_name") or "modelo"
    comparison = promotion_data.get("comparison", {})
    dataset_info = promotion_data.get("dataset_info", {})
    reason_text = comparison.get("reason")
    metric_name = comparison.get("metric_name") or "f1_oot"
    metric_current = comparison.get("metric_current")
    metric_previous = comparison.get("metric_previous")
    metric_delta = comparison.get("metric_delta")
    if metric_current is None and comparison.get("f1_oot_current") is not None:
        metric_name = "f1_oot"
        metric_current = comparison.get("f1_oot_current")
        metric_previous = comparison.get("f1_oot_previous")
        metric_delta = comparison.get("f1_oot_delta")

    current_run = promotion_data.get("current_run", {})
    previous_model = promotion_data.get("previous_model", {})
    promoted_at = promotion_data.get("promoted_at") or "não informado"

    dataset_lines = []
    for key, value in (dataset_info or {}).items():
        dataset_lines.append(f"- {key}: {value}")
    dataset_block = "\n".join(dataset_lines) if dataset_lines else "- não informado"

    metrics_lines = []
    if metric_current is not None:
        metrics_lines.append(f"- {metric_name} atual: {_format_metric_value(metric_current)}")
    if metric_previous is not None:
        metrics_lines.append(f"- {metric_name} anterior: {_format_metric_value(metric_previous)}")
    if metric_delta is not None:
        metrics_lines.append(f"- delta {metric_name}: {_format_delta_pp(metric_delta)}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "- não informado"

    if metric_current is not None and metric_previous is not None:
        current_fmt = _format_metric_value(metric_current)
        previous_fmt = _format_metric_value(metric_previous)
        if metric_current > metric_previous:
            reason_text = f"O {metric_name} subiu de {previous_fmt} para {current_fmt}."
        elif metric_current < metric_previous:
            reason_text = f"O {metric_name} caiu de {previous_fmt} para {current_fmt}."
        else:
            reason_text = f"O {metric_name} manteve {current_fmt}."
    if not reason_text:
        reason_text = "Sem comparação disponível."

    technical_subject = f"Promoção de modelo para produção: {model_name}"
    technical_content = (
        f"Modelo promovido: {model_name}\n"
        f"Momento da promoção: {promoted_at}\n"
        f"Run atual: {current_run.get('run_id') or 'não informado'}\n"
        f"Modelo anterior: {previous_model.get('name') or 'não informado'}\n"
        f"Run anterior: {previous_model.get('run_id') or 'não informado'}\n"
        f"Motivo: {reason_text}\n"
        f"Métricas ({metric_name}):\n{metrics_block}\n"
        f"Dataset:\n{dataset_block}\n"
    )
    executive_subject = f"Modelo em produção: {model_name}"
    executive_content = (
        f"Novo modelo promovido para produção: {model_name}.\n"
        f"Resumo: {reason_text}\n"
        f"{metric_name} atual: {_format_metric_value(metric_current)}\n"
        f"{metric_name} anterior: {_format_metric_value(metric_previous)}\n"
    )
    fallback_info = {"fallback": True, "reason": reason}
    return {
        "technical": {"subject": technical_subject, "content": technical_content},
        "executive": {"subject": executive_subject, "content": executive_content},
        "fallback_info": fallback_info,
    }


def generate_email_payload(promotion_data: Dict[str, Any], model_id: Optional[str] = None) -> Dict[str, Any]:
    model_id = model_id or get_configured_model_id()
    system_text = (
        "You draft email messages about fraud model promotions. "
        "Respond in pt-br. Return only JSON."
    )
    user_text = json.dumps(
        {
            "task": "Write two email drafts: one for technical team and one for executives.",
            "requirements": [
                "Use a clear subject.",
                "Explain the promotion reason and compare with the previous model.",
                "Mention dataset info when available.",
                "Keep executive email short and high level.",
                "Do not use markdown, bullet lists, or tables in the content.",
                "Use plain sentences only.",
                "Keep technical content under 1200 characters.",
                "Keep executive content under 600 characters.",
                "If you mention PPR, describe it as alert rate (Positive Prediction Rate), not false positive rate.",
            ],
            "output_format": {
                "technical": {"subject": "...", "content": "..."},
                "executive": {"subject": "...", "content": "..."},
            },
            "promotion_data": promotion_data,
        },
        ensure_ascii=True,
    )
    try:
        if _is_openai_model(model_id):
            messages = _build_openai_messages(system_text, user_text)
            text = _invoke_openai(messages, model_id)
        else:
            prompt = _build_llama_prompt(system_text, user_text)
            text = _invoke_llama(prompt, model_id)
    except Exception as ex:
        logger.exception("Bedrock invoke failed")
        return _build_fallback_email(promotion_data, str(ex))

    if not text or not text.strip():
        logger.warning("Bedrock returned an empty response for model_id=%s", model_id)
        return _build_fallback_email(promotion_data, "Resposta vazia do Bedrock.")

    parsed = _extract_json(text)
    if parsed and isinstance(parsed, dict):
        return parsed

    cleaned_preview = _sanitize_bedrock_text(text)
    logger.warning("Bedrock response was not valid JSON. Preview: %s", cleaned_preview[:2000])
    return _build_fallback_email(
        promotion_data,
        "Resposta do Bedrock não estava em JSON válido.",
    )

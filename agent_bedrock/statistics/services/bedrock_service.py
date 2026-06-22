import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0")
AWS_REGION = os.getenv(
    "BEDROCK_REGION",
    os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
)
DEFAULT_MAX_GEN_LEN = int(os.getenv("BEDROCK_MAX_GEN_LEN", "1800"))
DEFAULT_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.2"))
DEFAULT_TOP_P = float(os.getenv("BEDROCK_TOP_P", "0.9"))
BEDROCK_LOG_RAW_OUTPUT = os.getenv("BEDROCK_LOG_RAW_OUTPUT", "true").lower() == "true"
BEDROCK_LOG_RAW_OUTPUT_MAX_CHARS = int(os.getenv("BEDROCK_LOG_RAW_OUTPUT_MAX_CHARS", "50000"))


class BedrockEmailGenerationError(RuntimeError):
    pass


def _clip_for_log(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n...[truncated {len(text) - max_chars} chars]"


def _log_bedrock_output(stage: str, text: str) -> None:
    if not BEDROCK_LOG_RAW_OUTPUT:
        return
    clipped = _clip_for_log(str(text), BEDROCK_LOG_RAW_OUTPUT_MAX_CHARS)
    logger.warning(
        "BEDROCK_%s_BEGIN\n%s\nBEDROCK_%s_END",
        stage.upper(),
        clipped,
        stage.upper(),
    )


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
    for candidate in reversed(_extract_json_objects(cleaned)):
        if candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        for variant in _build_parse_variants(candidate):
            parsed = _try_parse_json(variant)
            payload = _coerce_to_email_payload(parsed)
            if payload is not None:
                return payload
    return None


def _sanitize_bedrock_text(text: str) -> str:
    cleaned = text.strip()
    for tag in ("reasoning", "thinking", "analysis", "thought"):
        open_tag = f"<{tag}>"
        close_tag = f"</{tag}>"
        if open_tag in cleaned and close_tag in cleaned:
            cleaned = cleaned.split(close_tag, 1)[1].strip()
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned


def _try_parse_json(candidate: str) -> Optional[Any]:
    for strict in (True, False):
        try:
            return json.loads(candidate, strict=strict)
        except json.JSONDecodeError:
            continue
    return None


def _extract_first_json_object(text: str) -> Optional[str]:
    objects = _extract_json_objects(text)
    return objects[0] if objects else None


def _extract_json_objects(text: str) -> List[str]:
    objects: List[str] = []
    depth = 0
    in_string = False
    escape = False
    start: Optional[int] = None
    for idx, ch in enumerate(text):
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
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : idx + 1])
                start = None
    return objects


def _coerce_to_email_payload(parsed: Any) -> Optional[Dict[str, Any]]:
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                return item
        return None
    if isinstance(parsed, str):
        nested = _try_parse_json(parsed)
        if isinstance(nested, dict):
            return nested
        if isinstance(nested, list):
            for item in nested:
                if isinstance(item, dict):
                    return item
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


def _format_float(value: Optional[float], decimals: int = 4) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.{decimals}f}"


def _format_percent(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.{decimals}f}%"


def _format_int(value: Any) -> str:
    if value is None:
        return "não informado"
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value)


def _format_signed_float(value: Optional[float], decimals: int = 6) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    prefix = "+" if numeric > 0 else ""
    return f"{prefix}{numeric:.{decimals}f}"


def _format_signed_int(value: Any) -> str:
    if value is None:
        return "não informado"
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        return str(value)
    prefix = "+" if numeric > 0 else ""
    return f"{prefix}{numeric}"


def _format_delta_pct(delta_pct: Optional[float], previous_value: Any) -> str:
    if delta_pct is None:
        if previous_value is not None:
            try:
                if float(previous_value) == 0:
                    return "variação percentual indisponível (base anterior igual a zero)"
            except (TypeError, ValueError):
                pass
        return "variação percentual indisponível"
    return f"{_format_signed_float(delta_pct, 2)}%"


def _build_quantitative_24h_texts(stats_data: Dict[str, Any]) -> Dict[str, str]:
    comparison = stats_data.get("comparison_24h", {}) or {}
    previous_window = str(comparison.get("previous_window") or "janela anterior").replace(" ate ", " até ")
    comp_scored = comparison.get("scored_count", {}) or {}
    comp_score = comparison.get("avg_score", {}) or {}
    comp_alerts = comparison.get("flagged_count", {}) or {}
    comp_scored_trend = str(comp_scored.get("trend", "indisponível")).replace("indisponivel", "indisponível")
    comp_score_trend = str(comp_score.get("trend", "indisponível")).replace("indisponivel", "indisponível")
    comp_alerts_trend = str(comp_alerts.get("trend", "indisponível")).replace("indisponivel", "indisponível")

    scored_delta = _format_signed_int(comp_scored.get("delta"))
    scored_pct = _format_delta_pct(comp_scored.get("delta_pct"), comp_scored.get("previous"))
    score_delta = _format_signed_float(comp_score.get("delta"), 6)
    score_pct = _format_delta_pct(comp_score.get("delta_pct"), comp_score.get("previous"))
    alerts_delta = _format_signed_int(comp_alerts.get("delta"))
    alerts_pct = _format_delta_pct(comp_alerts.get("delta_pct"), comp_alerts.get("previous"))

    comparison_text_technical = (
        f"Em comparação com as 24h anteriores ({previous_window}), o volume de transações {comp_scored_trend} "
        f"({scored_delta} transações; {scored_pct}), o score médio {comp_score_trend} "
        f"({score_delta}; {score_pct}) e o número de alertas {comp_alerts_trend} "
        f"({alerts_delta} alertas; {alerts_pct})."
    )
    comparison_text_executive = (
        f"Em relação às 24h anteriores, o volume de transações {comp_scored_trend} "
        f"({scored_delta}; {scored_pct}), o score médio {comp_score_trend} "
        f"({score_delta}; {score_pct}) e o número de alertas {comp_alerts_trend} "
        f"({alerts_delta}; {alerts_pct})."
    )
    return {
        "technical": comparison_text_technical,
        "executive": comparison_text_executive,
    }


def _build_python_comparison_texts(stats_data: Dict[str, Any]) -> Dict[str, str]:
    comparison_texts = _build_quantitative_24h_texts(stats_data)
    technical = comparison_texts["technical"]
    executive = comparison_texts["executive"]
    comparison = stats_data.get("comparison_24h", {}) or {}
    model_context = comparison.get("model_context", {}) or {}
    if model_context.get("promoted_in_last_48h"):
        note = " Houve promoção recente de modelo e a comparação pode refletir troca de versão."
        technical += note
        executive += note
    return {"technical": technical, "executive": executive}


def _normalize_spaces(text: str) -> str:
    return " ".join(str(text).split())


def _contains_normalized(haystack: str, needle: str) -> bool:
    normalized_haystack = _normalize_spaces(haystack).lower()
    normalized_needle = _normalize_spaces(needle).lower()
    return normalized_needle in normalized_haystack


def _replace_or_append_comparison(content: str, expected_text: str) -> str:
    text = str(content).strip()
    if not text:
        return expected_text

    if _contains_normalized(text, expected_text):
        return text

    if text.endswith((".", "!", "?")):
        return f"{text} {expected_text}"
    return f"{text}. {expected_text}"


def _enforce_python_comparison(payload: Dict[str, Any], stats_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return payload

    expected = _build_python_comparison_texts(stats_data)
    result = dict(payload)

    technical = result.get("technical")
    if isinstance(technical, dict):
        technical_section = dict(technical)
        technical_content = str(technical_section.get("content", "")).strip()
        technical_section["content"] = _replace_or_append_comparison(technical_content, expected["technical"])
        result["technical"] = technical_section

    executive = result.get("executive")
    if isinstance(executive, dict):
        executive_section = dict(executive)
        executive_content = str(executive_section.get("content", "")).strip()
        executive_section["content"] = _replace_or_append_comparison(executive_content, expected["executive"])
        result["executive"] = executive_section

    return result


def _format_window(window: Dict[str, Any]) -> str:
    mode = window.get("mode")
    if mode == "partition_hourly":
        start = window.get("start") or "?"
        end = window.get("end") or "?"
        return f"{start} até {end}"
    if mode == "partition_daily":
        date = window.get("date") or "?"
        return f"data {date}"
    if mode == "lookback_hours":
        hours = window.get("hours") or "?"
        return f"últimas {hours} horas"
    return "janela não informada"


def _build_llm_stats_data(stats_data: Dict[str, Any]) -> Dict[str, Any]:
    model = stats_data.get("model", {}) or {}
    experiment = (model.get("experiment") or {}) if isinstance(model, dict) else {}
    comparison = stats_data.get("comparison_24h", {}) or {}
    model_context = comparison.get("model_context", {}) or {}

    return {
        "status": stats_data.get("status"),
        "missing": stats_data.get("missing"),
        "window_summary": stats_data.get("window_summary"),
        "metrics": stats_data.get("metrics"),
        "comparison_24h": {
            "previous_window": comparison.get("previous_window"),
            "scored_count": comparison.get("scored_count"),
            "avg_score": comparison.get("avg_score"),
            "flagged_count": comparison.get("flagged_count"),
            "model_context": {
                "current_model_name": model_context.get("current_model_name") or experiment.get("name"),
                "promotion_time": model_context.get("promotion_time"),
                "promoted_in_last_48h": model_context.get("promoted_in_last_48h"),
            },
        },
        "distribution_summary_percent": stats_data.get("distribution_summary_percent"),
        "threshold": {
            "current_model_value": ((stats_data.get("threshold", {}) or {}).get("current_model_value")),
            "current_model_value_source": ((stats_data.get("threshold", {}) or {}).get("current_model_value_source")),
            "value": ((stats_data.get("threshold", {}) or {}).get("value")),
            "source": ((stats_data.get("threshold", {}) or {}).get("source")),
        },
        "model": {
            "experiment": {
                "name": experiment.get("name"),
            }
        },
    }


def _build_fallback_email(stats_data: Dict[str, Any], reason: Optional[str]) -> Dict[str, Any]:
    status = stats_data.get("status") or "unknown"
    model_name = (
        (stats_data.get("model", {}) or {}).get("experiment", {}) or {}
    ).get("name") or "modelo"
    window_text = (stats_data.get("window_summary") or _format_window(stats_data.get("window", {}) or {})).replace(" ate ", " até ")

    metrics = stats_data.get("metrics", {}) or {}
    scored_count = _format_int(metrics.get("scored_count"))
    avg_score = _format_float(metrics.get("avg_score"), 6)
    flagged_count = _format_int(metrics.get("flagged_count"))
    flagged_rate_pct = _format_percent(metrics.get("flagged_rate_pct"), 4)

    distribution_summary = stats_data.get("distribution_summary_percent")
    dist_text = f"Distribuição (score): {distribution_summary}" if distribution_summary else "Distribuição (score): indisponível"

    threshold = stats_data.get("threshold", {}) or {}
    threshold_value = threshold.get("current_model_value", threshold.get("value"))
    threshold_text = _format_float(threshold_value, 6)
    threshold_source = threshold.get("current_model_value_source", threshold.get("source", "indisponível"))

    comparison_texts = _build_python_comparison_texts(stats_data)
    comparison_text_technical = comparison_texts["technical"]
    comparison_text_executive = comparison_texts["executive"]

    missing = stats_data.get("missing") or []
    missing_text = ""
    if status == "missing_config" and missing:
        missing_text = f" Configuração faltante: {', '.join(missing)}."

    technical_subject = f"Relatório técnico de monitoramento - {model_name}"
    technical_content = (
        f"O monitoramento do modelo {model_name} no período {window_text} terminou com status {status}.{missing_text}\n"
        f"Foram avaliadas {scored_count} transações, com score médio de {avg_score}, {flagged_count} alertas e PPR de {flagged_rate_pct}.\n"
        f"{dist_text}.\n"
        f"O threshold vigente do modelo em produção é {threshold_text} (fonte: {threshold_source}).\n"
        f"{comparison_text_technical}"
    )
    executive_subject = f"Resumo diário de fraude - {model_name}"
    executive_content = (
        f"No período {window_text}, o modelo operou com status {status}, analisou {scored_count} transações e registrou PPR de {flagged_rate_pct}. "
        f"{comparison_text_executive}"
    )
    fallback_info = {"fallback": True, "reason": reason}
    return {
        "technical": {"subject": technical_subject, "content": technical_content},
        "executive": {"subject": executive_subject, "content": executive_content},
        "fallback_info": fallback_info,
    }


def _extract_email_section(payload: Dict[str, Any], section_name: str) -> Optional[Dict[str, str]]:
    if not isinstance(payload, dict):
        return None
    section = payload.get(section_name)
    if not isinstance(section, dict):
        return None
    subject = str(section.get("subject", "")).strip()
    content = str(section.get("content", "")).strip()
    if not subject or not content:
        return None
    return {"subject": subject, "content": content}


def _recover_email_payload(
    stats_data: Dict[str, Any], reason: str, *payloads: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    fallback = _build_fallback_email(stats_data, reason)

    def _collect_candidates(section_name: str) -> List[Dict[str, str]]:
        candidates: List[Dict[str, str]] = []
        seen = set()
        for payload in payloads:
            section = _extract_email_section(payload, section_name)
            if not section:
                continue
            key = (section["subject"], section["content"])
            if key in seen:
                continue
            seen.add(key)
            candidates.append(section)

        fallback_section = fallback[section_name]
        fallback_key = (fallback_section["subject"], fallback_section["content"])
        if fallback_key not in seen:
            candidates.append(fallback_section)
        return candidates

    technical_candidates = _collect_candidates("technical")
    executive_candidates = _collect_candidates("executive")
    fallback_technical = fallback["technical"]
    fallback_executive = fallback["executive"]

    for technical in technical_candidates:
        for executive in executive_candidates:
            candidate = _enforce_python_comparison(
                {
                    "technical": dict(technical),
                    "executive": dict(executive),
                },
                stats_data,
            )
            if _validate_email_payload(candidate, stats_data):
                continue
            used_fallback = technical == fallback_technical or executive == fallback_executive
            if used_fallback:
                candidate["fallback_info"] = {
                    "fallback": True,
                    "reason": reason,
                }
            return candidate
    return None


def _fill_missing_email_sections(payload: Dict[str, Any], stats_data: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _build_fallback_email(stats_data, "preenchimento_local_de_secao_faltante")
    result: Dict[str, Any] = dict(payload) if isinstance(payload, dict) else {}
    for section_name in ("technical", "executive"):
        section = _extract_email_section(result, section_name)
        if section is not None:
            result[section_name] = section
            continue
        result[section_name] = dict(fallback[section_name])
    return result


def _validate_email_payload(payload: Dict[str, Any], stats_data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    technical = payload.get("technical")
    executive = payload.get("executive")
    if not isinstance(technical, dict):
        issues.append("missing_technical")
    if not isinstance(executive, dict):
        issues.append("missing_executive")
    if issues:
        return issues

    technical_subject = str(technical.get("subject", "")).strip()
    technical_content = str(technical.get("content", "")).strip()
    executive_subject = str(executive.get("subject", "")).strip()
    executive_content = str(executive.get("content", "")).strip()
    if not technical_subject or not technical_content:
        issues.append("empty_technical_fields")
    if not executive_subject or not executive_content:
        issues.append("empty_executive_fields")

    lowered_exec = executive_content.lower()
    if "distribuicao" in lowered_exec or "distribuição" in lowered_exec or "p50" in lowered_exec or "p90" in lowered_exec or "p95" in lowered_exec or "p99" in lowered_exec:
        issues.append("executive_contains_distribution")
    if "threshold" in lowered_exec:
        issues.append("executive_contains_threshold")

    if "24h anteriores" not in technical_content.lower() and "24h anteriores" not in executive_content.lower():
        issues.append("missing_24h_comparison")

    expected_comparison = _build_python_comparison_texts(stats_data)
    if not _contains_normalized(technical_content, expected_comparison["technical"]):
        issues.append("technical_comparison_not_python_computed")
    if not _contains_normalized(executive_content, expected_comparison["executive"]):
        issues.append("executive_comparison_not_python_computed")

    distribution_summary = stats_data.get("distribution_summary_percent")
    if distribution_summary and distribution_summary not in technical_content:
        issues.append("missing_distribution_summary_in_technical")

    threshold = stats_data.get("threshold", {}) or {}
    threshold_value = threshold.get("current_model_value", threshold.get("value"))
    if threshold_value is not None:
        threshold_tokens = {
            _format_float(threshold_value, 6),
            _format_float(threshold_value, 4),
        }
        try:
            threshold_tokens.add(str(float(threshold_value)))
        except (TypeError, ValueError):
            pass
        threshold_tokens.update(token.replace(".", ",") for token in list(threshold_tokens))
        if not any(token and token in technical_content for token in threshold_tokens):
            issues.append("missing_threshold_value_in_technical")

    return issues


def generate_email_payload(stats_data: Dict[str, Any], model_id: Optional[str] = None) -> Dict[str, Any]:
    model_id = model_id or get_configured_model_id()
    precomputed_comparison_text = _build_python_comparison_texts(stats_data)
    llm_stats_data = _build_llm_stats_data(stats_data)
    requirements = [
        "Use a clear subject.",
        "Summarize the monitoring window and key metrics.",
        "Use model B style: technical detailed, executive concise.",
        "Include 24h current vs previous comparison for volume, average score, and number of alerts.",
        "When comparing with the previous 24h, always include quantitative deltas (absolute change and percentage change when available).",
        "Do not calculate 24h deltas yourself; use the values provided in comparison_24h_text_precomputed.",
        "Use comparison_24h_text_precomputed.technical exactly in technical content.",
        "Use comparison_24h_text_precomputed.executive exactly in executive content.",
        "If window_summary is present, preserve the same time values and write it in correct pt-BR (e.g., use 'até').",
        "Do not include seconds, milliseconds, or timezone suffix in the window text.",
        "Include scored count, average score, and flagged rate when available.",
        "If distribution_summary_percent is present, include it exactly as provided in technical email only.",
        "Include current model threshold value in technical email only.",
        "Executive email must not include threshold or score distribution.",
        "If comparison_24h.model_context.promoted_in_last_48h is true, mention that comparison may reflect model version change.",
        "Avoid scientific notation for score distribution.",
        "Do not mention latency when no latency data is present.",
        "Do not use markdown, bullet lists, or tables in the content.",
        "Use plain sentences only.",
        "Return only JSON, without <reasoning> tags or analysis text.",
        "Keep technical content under 1200 characters.",
        "Keep executive content under 600 characters.",
        "If you mention PPR, describe it as alert rate (Positive Prediction Rate), not false positive rate.",
    ]

    system_text = (
        "You draft email messages about fraud model monitoring statistics. "
        "Respond in pt-BR with proper accents and cedilla. "
        "Return only JSON and do not output reasoning tags."
    )

    def _invoke_with_payload(payload: Dict[str, Any]) -> str:
        user_text = json.dumps(payload, ensure_ascii=True)
        if _is_openai_model(model_id):
            messages = _build_openai_messages(system_text, user_text)
            return _invoke_openai(messages, model_id)
        prompt = _build_llama_prompt(system_text, user_text)
        return _invoke_llama(prompt, model_id)

    def _extract_missing_sections(validation_errors: List[str]) -> List[str]:
        sections: List[str] = []
        if "missing_technical" in validation_errors or "empty_technical_fields" in validation_errors:
            sections.append("technical")
        if "missing_executive" in validation_errors or "empty_executive_fields" in validation_errors:
            sections.append("executive")
        if sections:
            return sections
        return ["technical", "executive"]

    def _attempt_parse_and_validate(stage: str, response_text: str):
        _log_bedrock_output(stage, response_text)
        if not response_text or not str(response_text).strip():
            return None, ["empty_response"]

        candidate = _extract_json(response_text)
        if candidate and isinstance(candidate, dict):
            _log_bedrock_output(f"{stage}_parsed_json", json.dumps(candidate, ensure_ascii=False))
            return candidate, _validate_email_payload(candidate, stats_data)

        cleaned_preview = _sanitize_bedrock_text(response_text)
        logger.warning("Bedrock %s was not valid JSON. Preview: %s", stage, cleaned_preview[:2000])
        return None, ["invalid_json"]

    initial_payload = {
        "task": "Write two email drafts: one for technical team and one for executives.",
        "requirements": requirements,
        "comparison_24h_text_precomputed": precomputed_comparison_text,
        "output_format": {
            "technical": {"subject": "...", "content": "..."},
            "executive": {"subject": "...", "content": "..."},
        },
        "stats_data": llm_stats_data,
    }

    try:
        text = _invoke_with_payload(initial_payload)
    except Exception as ex:
        logger.exception("Bedrock invoke failed")
        raise BedrockEmailGenerationError(f"Falha ao invocar Bedrock: {ex}") from ex

    parsed, issues = _attempt_parse_and_validate("initial_response", text)
    if parsed and not issues:
        return parsed
    logger.warning("Bedrock initial payload invalid, attempting repair. issues=%s", issues)

    repair_payload = {
        "task": "Fix the invalid email JSON output. Return only corrected JSON.",
        "requirements": requirements,
        "validation_errors": issues,
        "invalid_output": parsed if isinstance(parsed, dict) else None,
        "raw_output_text": _sanitize_bedrock_text(text)[:20000],
        "comparison_24h_text_precomputed": precomputed_comparison_text,
        "output_format": {
            "technical": {"subject": "...", "content": "..."},
            "executive": {"subject": "...", "content": "..."},
        },
        "stats_data": llm_stats_data,
    }
    try:
        repair_text = _invoke_with_payload(repair_payload)
    except Exception as ex:
        logger.exception("Bedrock repair invoke failed")
        raise BedrockEmailGenerationError(f"Falha no repair via Bedrock: {ex}") from ex

    repaired, repair_issues = _attempt_parse_and_validate("repair_response", repair_text)
    if repaired and not repair_issues:
        return repaired

    logger.warning("Bedrock repair invalid, attempting targeted repair. issues=%s", repair_issues)
    missing_sections = _extract_missing_sections(repair_issues)
    targeted_requirements = [
        "Return only a valid JSON object with keys technical and executive.",
        "Do not output reasoning tags, analysis text, markdown, or code fences.",
        "If one section is valid in existing_output, keep it and fill only missing/invalid section.",
        "Use comparison_24h_text_precomputed.technical exactly in technical content.",
        "Use comparison_24h_text_precomputed.executive exactly in executive content.",
    ]
    targeted_payload = {
        "task": "Complete missing or invalid sections in the email JSON output.",
        "requirements": targeted_requirements,
        "missing_sections": missing_sections,
        "existing_output": repaired if isinstance(repaired, dict) else parsed if isinstance(parsed, dict) else None,
        "validation_errors": repair_issues,
        "comparison_24h_text_precomputed": precomputed_comparison_text,
        "output_format": {
            "technical": {"subject": "...", "content": "..."},
            "executive": {"subject": "...", "content": "..."},
        },
        "stats_data": llm_stats_data,
    }
    try:
        targeted_text = _invoke_with_payload(targeted_payload)
    except Exception as ex:
        logger.exception("Bedrock targeted repair invoke failed")
        raise BedrockEmailGenerationError(f"Falha no repair direcionado via Bedrock: {ex}") from ex

    targeted, targeted_issues = _attempt_parse_and_validate("targeted_repair_response", targeted_text)
    if targeted and not targeted_issues:
        return targeted

    logger.warning("Bedrock targeted repair still invalid. issues=%s", targeted_issues)
    final_issues = targeted_issues or repair_issues or issues or ["invalid_json"]
    raise BedrockEmailGenerationError(
        f"Resposta inválida após repairs via Bedrock: {', '.join(final_issues)}"
    )

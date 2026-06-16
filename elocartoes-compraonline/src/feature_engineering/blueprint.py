from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, IPv4Address
from typing import Any, Dict, Iterable, Mapping, Optional


PAN_REGEX = re.compile(r"^\d{13,19}$")


def _safe_get(d: Mapping[str, Any], path: Iterable[str], default: Any = None) -> Any:
    cur: Any = d
    for key in path:
        if not isinstance(cur, Mapping) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int,)):
            return value
        s = str(value).strip()
        if s == "":
            return default
        return int(s)
    except Exception:
        return default


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        if isinstance(value, (float, int)):
            return float(value)
        s = str(value).replace(",", ".").strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default


def _parse_amount(amount_str: Any, exponent_str: Any, default_exponent: int = 2) -> Optional[float]:
    amount_i = _to_int(amount_str)
    if amount_i is None:
        return None
    exp = _to_int(exponent_str, default_exponent)
    try:
        return amount_i * (10 ** -(exp if exp is not None else default_exponent))
    except Exception:
        return None


def _parse_purchase_date(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    s = str(ts).strip()
    if not s:
        return None
    # Expecting YYYYMMDDHHMMSS
    try:
        dt = datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _apply_tz_offset(dt: datetime, offset_minutes: Optional[int]) -> datetime:
    if offset_minutes is None:
        return dt
    try:
        return dt + timedelta(minutes=int(offset_minutes))
    except Exception:
        return dt


def _as_flag(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().upper()
    if s in {"Y", "YES", "TRUE", "1", "01"}:
        return True
    if s in {"N", "NO", "FALSE", "0", "02"}:
        return False
    return None


def _is_valid_pan_format(pan: Any) -> bool:
    if pan is None:
        return False
    return bool(PAN_REGEX.match(str(pan)))


def _luhn_check(pan: str) -> bool:
    try:
        digits = [int(c) for c in pan]
        checksum = 0
        parity = len(digits) % 2
        for i, d in enumerate(digits):
            if i % 2 == parity:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0
    except Exception:
        return False


def _hash_pan(pan: str, salt: str) -> str:
    # Do not store raw PAN; hash with secret salt provided outside code.
    h = hashlib.sha256()
    h.update((salt + pan).encode("utf-8"))
    return h.hexdigest()


def _bin6(pan: str) -> Optional[str]:
    return pan[:6] if pan and len(pan) >= 6 else None


def _bin8(pan: str) -> Optional[str]:
    return pan[:8] if pan and len(pan) >= 8 else None


def _ip_to_prefix24(ip: str) -> Optional[str]:
    try:
        ip_obj = ip_address(ip)
        if isinstance(ip_obj, IPv4Address):
            parts = str(ip_obj).split(".")
            return ".".join(parts[:3]) + ".0/24"
        # For IPv6, use /48 as a rough grouping
        return str(ip_obj).split(":")[0] + "::/48"
    except Exception:
        return None


def _amount_bucket(amount: Optional[float]) -> Optional[str]:
    if amount is None:
        return None
    # Simple heuristic buckets; tune offline via quantis
    if amount < 50:
        return "low"
    if amount < 200:
        return "mid"
    if amount < 1000:
        return "high"
    return "very_high"


@dataclass
class Enricher:
    """Stub interface for enrichment services (BIN, GeoIP, email, etc.).

    Replace these methods with real implementations wired to providers.
    """

    def bin_lookup(self, bin6_or_8: str) -> Dict[str, Any]:
        return {}

    def geoip(self, ip: str) -> Dict[str, Any]:
        return {}

    def is_disposable_email(self, domain: str) -> Optional[bool]:
        return None


@dataclass
class FeatureStoreClient:
    """Stub interface for a (near) real-time feature store client."""

    def get_features(
        self,
        entity: str,
        keys: Mapping[str, Any],
        feature_names: Iterable[str],
    ) -> Dict[str, Any]:
        return {}


class FeatureExtractor:
    """Blueprint to extract fraud features from the request payload.

    This class focuses on direct features from the payload and provides hooks
    for enrichment (BIN, GeoIP) and aggregated features via a Feature Store.

    Privacy: never return raw PAN, email, or PII. Only derived, non-reversible
    artifacts like BIN6/8 and hashes should be exposed.
    """

    def __init__(
        self,
        hash_salt: Optional[str] = None,
        enricher: Optional[Enricher] = None,
        feature_store: Optional[FeatureStoreClient] = None,
    ) -> None:
        self.hash_salt = hash_salt or "CHANGE_ME_SALT"
        self.enricher = enricher
        self.feature_store = feature_store

    def transform(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        features: Dict[str, Any] = {}
        features.update(self._extract_direct_features(payload))
        features.update(self._extract_enriched_features(payload))
        features.update(self._extract_aggregated_features(payload))
        return features

    # -------------------- Direct features --------------------
    def _extract_direct_features(self, p: Mapping[str, Any]) -> Dict[str, Any]:
        f: Dict[str, Any] = {}

        # Amount normalization
        amount = _parse_amount(p.get("purchase_amount"), p.get("purchase_exponent"))
        f["f_amount_value"] = amount
        f["f_amount_log"] = math.log1p(amount) if amount is not None else None
        f["f_amount_bucket"] = _amount_bucket(amount)

        # Installments / quick withdrawal
        f["f_installments_n"] = _to_int(p.get("purchase_instal_data"), 1)
        f["f_is_quick_withdrawal"] = bool(p.get("is_quick_withdrawal")) if p.get("is_quick_withdrawal") is not None else None

        # Temporal features
        purchase_dt = _parse_purchase_date(p.get("purchase_date"))
        tz_offset = _to_int(p.get("browser_tz"))
        if purchase_dt:
            local_dt = _apply_tz_offset(purchase_dt, tz_offset)
            f["f_weekend"] = local_dt.weekday() >= 5
            f["f_hour_local"] = local_dt.hour
        else:
            f["f_weekend"] = None
            f["f_hour_local"] = None

        # Address match and consistency
        f["f_addr_match"] = _as_flag(p.get("addr_match"))
        bill_country = _safe_get(p, ["billing_address", "country"]) or None
        ship_country = _safe_get(p, ["shipping_address", "country"]) or None
        f["f_bill_ship_country_match"] = (bill_country == ship_country) if (bill_country and ship_country) else None

        # Account behavior (from payload)
        f["f_nb_purchase_account"] = _to_int(_safe_get(p, ["acct_info", "nb_purchase_account"]))
        day = _to_int(_safe_get(p, ["acct_info", "txn_activity_day"]))
        year = _to_int(_safe_get(p, ["acct_info", "txn_activity_year"]))
        f["f_txn_activity_day"] = day
        f["f_txn_activity_ratio"] = (day / max(year or 0, 1)) if day is not None else None
        f["f_suspicious_acc_activity"] = _as_flag(_safe_get(p, ["acct_info", "suspicious_acc_activity"]))

        # 3DS, MCC, channel
        f["f_device_channel"] = p.get("device_channel")
        f["f_mcc"] = p.get("mcc")
        f["f_3ds_status"] = p.get("three_ds_trans_status")
        f["f_3ds_eci"] = p.get("three_ds_eci")

        # Browser / device
        f["f_js_enabled"] = bool(p.get("browser_javascript_enabled")) if p.get("browser_javascript_enabled") is not None else None
        f["f_java_enabled"] = bool(p.get("browser_java_enabled")) if p.get("browser_java_enabled") is not None else None
        f["f_browser_lang"] = p.get("browser_language")
        f["f_color_depth"] = _to_int(p.get("browser_color_depth"))
        f["f_screen_w"] = _to_int(p.get("browser_screen_width"))
        f["f_screen_h"] = _to_int(p.get("browser_screen_height"))
        f["f_tz_offset_min"] = tz_offset

        # UA parsing (very lightweight heuristic)
        ua = p.get("browser_user_agent") or ""
        ua_up = ua.upper()
        ua_family = (
            "CHROME" if "CHROME/" in ua_up else
            "SAFARI" if "SAFARI/" in ua_up else
            "FIREFOX" if "FIREFOX" in ua_up else
            "EDGE" if "EDG/" in ua_up else
            "OTHER"
        ) if ua else None
        ua_os = (
            "ANDROID" if "ANDROID" in ua_up else
            "IOS" if "IPHONE" in ua_up or "IPAD" in ua_up else
            "WINDOWS" if "WINDOWS" in ua_up else
            "MACOS" if "MAC OS" in ua_up or "MACOS" in ua_up else
            "LINUX" if "LINUX" in ua_up else
            "OTHER"
        ) if ua else None
        f["f_user_agent_family"] = ua_family
        f["f_user_agent_os"] = ua_os

        # Currency and merchant info
        f["f_currency_iso3"] = p.get("purchase_currency")
        f["f_merchant_country_code"] = p.get("merchant_country_code")
        f["f_is_direct_selling"] = bool(p.get("is_direct_selling")) if p.get("is_direct_selling") is not None else None

        # Gift card and recurring
        gift_amount = _to_float(_safe_get(p, ["merchant_risk_indicator", "gift_card_amount"]))
        f["f_gift_card_count"] = _to_int(_safe_get(p, ["merchant_risk_indicator", "gift_card_count"]))
        f["f_gift_card_amount_ratio"] = (gift_amount / amount) if (gift_amount is not None and amount and amount > 0) else None
        f["f_pre_order_ind"] = _as_flag(_safe_get(p, ["merchant_risk_indicator", "pre_order_purchase_ind"]))

        # Recurring indicators
        f["f_recurring_amount_ind"] = _safe_get(p, ["recurring_ind", "amount_ind"]) or None
        f["f_recurring_frequency_ind"] = _safe_get(p, ["recurring_ind", "frequency_ind"]) or None

        # COF recency (in days)
        cof_date_str = _safe_get(p, ["payment_info", "cof_date"]) or None
        if cof_date_str:
            try:
                # Accept ISO-like formats; naive fallback
                try:
                    cof_dt = datetime.fromisoformat(cof_date_str.replace("Z", "+00:00"))
                except Exception:
                    cof_dt = datetime.strptime(cof_date_str, "%Y-%m-%dT%H:%M:%S%z")
                now = datetime.now(timezone.utc)
                # If parsed naive, localize to UTC
                if cof_dt.tzinfo is None:
                    cof_dt = cof_dt.replace(tzinfo=timezone.utc)
                f["f_cof_recency_days"] = (now - cof_dt).total_seconds() / 86400.0
            except Exception:
                f["f_cof_recency_days"] = None
        else:
            f["f_cof_recency_days"] = None

        # Quality flags
        pan = p.get("card_number")
        f["q_invalid_pan_format"] = (not _is_valid_pan_format(pan)) if pan is not None else None
        f["q_invalid_email_format"] = ("@" not in str(p.get("email"))) if p.get("email") is not None else None
        postal = _safe_get(p, ["billing_address", "postal_code"]) or None
        f["q_postal_code_invalid_len"] = (len(postal) < 5) if postal is not None else None
        f["q_user_agent_missing"] = (len(ua) < 10) if ua is not None else None
        f["q_missing_exponent"] = (p.get("purchase_exponent") is None)

        return f

    # -------------------- Enriched features --------------------
    def _extract_enriched_features(self, p: Mapping[str, Any]) -> Dict[str, Any]:
        f: Dict[str, Any] = {}

        pan = p.get("card_number")
        if _is_valid_pan_format(pan):
            # Hash (do not expose raw PAN)
            f["card_hash"] = _hash_pan(str(pan), self.hash_salt)
            # BINs
            bin6 = _bin6(str(pan))
            bin8 = _bin8(str(pan))
            f["enr_card_bin6"] = bin6
            f["enr_card_bin8"] = bin8
            f["enr_card_luhn_valid"] = _luhn_check(str(pan))

            # Optional BIN lookup
            if self.enricher and (bin8 or bin6):
                lookup_key = bin8 or bin6  # prefer bin8
                try:
                    info = self.enricher.bin_lookup(lookup_key) or {}
                except Exception:
                    info = {}
                f.update({
                    "enr_card_brand": info.get("brand"),
                    "enr_card_type": info.get("type"),
                    "enr_card_product": info.get("product"),
                    "enr_issuer_country": info.get("issuer_country"),
                })
        else:
            f["card_hash"] = None
            f["enr_card_bin6"] = None
            f["enr_card_bin8"] = None
            f["enr_card_luhn_valid"] = None

        # IP-based enrichment
        ip = p.get("browser_ip")
        if ip and self.enricher:
            try:
                geo = self.enricher.geoip(ip) or {}
            except Exception:
                geo = {}
            f.update({
                "enr_ip_country": geo.get("country"),
                "enr_ip_region": geo.get("region"),
                "enr_ip_city": geo.get("city"),
                "enr_ip_asn": geo.get("asn"),
                "enr_ip_is_proxy_vpn": geo.get("is_proxy_vpn"),
            })
            # Simple IP prefix grouping
            f["ip_prefix24"] = _ip_to_prefix24(ip)
        else:
            f["ip_prefix24"] = _ip_to_prefix24(ip) if ip else None

        # Email domain and disposable check
        email = p.get("email") or ""
        domain = email.split("@")[-1] if "@" in email else None
        f["enr_email_domain"] = domain
        if domain and self.enricher:
            try:
                f["enr_email_is_disposable"] = self.enricher.is_disposable_email(domain)
            except Exception:
                f["enr_email_is_disposable"] = None
        else:
            f["enr_email_is_disposable"] = None

        return f

    # -------------------- Aggregated features --------------------
    def _extract_aggregated_features(self, p: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.feature_store:
            return {}

        feats: Dict[str, Any] = {}

        # Entities and keys
        card_hash = None
        pan = p.get("card_number")
        if _is_valid_pan_format(pan):
            card_hash = _hash_pan(str(pan), self.hash_salt)

        device_hash = _safe_get(p, ["device_info", "hash"]) or None
        email = p.get("email") or None
        merchant_id = p.get("acquirer_merchant_id") or None
        merchant_document = p.get("merchant_document") or None
        mcc = p.get("mcc") or None
        ip_prefix = _ip_to_prefix24(p.get("browser_ip") or "")

        # Queries (stubs)
        try:
            if card_hash:
                feats.update(self.feature_store.get_features(
                    entity="card",
                    keys={"card_hash": card_hash},
                    feature_names=[
                        "txn_24h_count",
                        "txn_7d_count",
                        "ticket_30d_mean",
                        "ticket_30d_std",
                        "chargeback_rate_90d",
                        "geo_countries_30d_nunique",
                    ],
                ))
            if device_hash:
                feats.update(self.feature_store.get_features(
                    entity="device",
                    keys={"device_hash": device_hash},
                    feature_names=["cards_7d_nunique"],
                ))
            if ip_prefix:
                feats.update(self.feature_store.get_features(
                    entity="ip_prefix",
                    keys={"prefix": ip_prefix},
                    feature_names=["cards_24h_nunique"],
                ))
            if email:
                feats.update(self.feature_store.get_features(
                    entity="email",
                    keys={"email": email},
                    feature_names=["merchants_30d_nunique"],
                ))
            if merchant_id:
                feats.update(self.feature_store.get_features(
                    entity="merchant",
                    keys={"acquirer_merchant_id": merchant_id},
                    feature_names=["devices_7d_nunique"],
                ))
            # Examples for pair entities could be added similarly
        except Exception:
            # In blueprint mode, ignore feature-store failures gracefully
            pass

        # Prefix features to align with spec naming (optional)
        mapped: Dict[str, Any] = {}
        for k, v in feats.items():
            # Map some common ones to spec-like names
            if k == "txn_24h_count":
                mapped["agg_card_txn_24h_count"] = v
            elif k == "txn_7d_count":
                mapped["agg_card_txn_7d_count"] = v
            elif k == "ticket_30d_mean":
                mapped["agg_card_ticket_30d_mean"] = v
            elif k == "ticket_30d_std":
                mapped["agg_card_ticket_30d_std"] = v
            elif k == "chargeback_rate_90d":
                mapped["agg_card_chargeback_rate_90d"] = v
            elif k == "geo_countries_30d_nunique":
                mapped["agg_geo_card_countries_30d_nunique"] = v
            elif k == "cards_7d_nunique":
                mapped["agg_device_cards_7d_nunique"] = v
            elif k == "cards_24h_nunique":
                mapped["agg_ip_cards_24h_nunique"] = v
            elif k == "merchants_30d_nunique":
                mapped["agg_email_merchants_30d_nunique"] = v
            elif k == "devices_7d_nunique":
                mapped["agg_merchant_devices_7d_nunique"] = v
            else:
                mapped[k] = v

        return mapped


__all__ = [
    "FeatureExtractor",
    "Enricher",
    "FeatureStoreClient",
]


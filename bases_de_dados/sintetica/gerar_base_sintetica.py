from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import numpy as np
import pandas as pd
import yaml
from faker import Faker
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "076": {"locale": "pt_BR"},
    "840": {"locale": "en_US"},
    "250": {"locale": "fr_FR"},
}


@dataclass
class ScenarioSpec:
    name: str
    weight: float
    volume: Optional[int]
    profile: str
    field_specs: Dict[str, Dict[str, Any]]
    options: Dict[str, Dict[str, Any]]


@dataclass
class Usuario:
    cardHolderDocument: str
    cardholderName: str
    acctNumber: str
    cardExpiryDate: str
    email: str
    billAddrLine1: str
    billAddrLine2: str
    billAddrCity: str
    billAddrState: str
    billAddrCountry: str
    billAddrPostCode: str


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class SyntheticPurchaseGenerator:
    def __init__(self, config: Dict[str, Any], config_path: Path) -> None:
        self.config = config
        self.config_path = config_path
        self.seed: int = int(config["geracao"]["seed"])
        self.rng = np.random.default_rng(self.seed)
        Faker.seed(self.seed)
        self.fakers: Dict[str, Faker] = {
            "pt_BR": Faker("pt_BR"),
            "en_US": Faker("en_US"),
            "es_ES": Faker("es_ES"),
            "fr_FR": Faker("fr_FR"),
        }
        self.validator = self._build_validator()
        self.common_fields = config.get("campos_comuns", {})
        self.monetary_profiles = config.get("valores_monetarios", {})
        self.required_fields: Sequence[str] = config.get("campos_obrigatorios", [])
        self.label_cfg = config.get("rotulo_fraude", {})
        self.label_field: Optional[str] = None
        self.label_default_prob: float = 0.0
        self.label_probs: Dict[str, float] = {}
        if self.label_cfg:
            self.label_field = self.label_cfg.get("campo", "fraud_label")
            self.label_default_prob = float(self.label_cfg.get("probabilidade_padrao", 0.0))
            self.label_probs = {
                str(key): float(value)
                for key, value in self.label_cfg.get("probabilidades_por_cenario", {}).items()
            }
            formato = self.label_cfg.get("formato", "int")
            if formato not in {"int", "bool", "str"}:
                raise ValueError(f"Formato de rótulo inválido: {formato}")
            self.label_format = formato
        else:
            self.label_format = "int"
        self.scenarios = self._prepare_scenarios(config.get("cenarios", []))

    def _build_validator(self) -> Draft202012Validator:
        schema_relative = self.config["geracao"]["schema_path"]
        schema_path = (self.config_path.parent / schema_relative).resolve()
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema não encontrado em {schema_path}")
        try:
            with schema_path.open(encoding="utf-8") as handle:
                spec = json.load(handle)
        except json.JSONDecodeError:
            with schema_path.open(encoding="utf-8") as handle:
                spec = yaml.safe_load(handle)
        components = spec.get("components", {})
        schema_root = {
            "$ref": "#/components/schemas/OnlinePurchaseRequest",
            "components": components,
        }
        return Draft202012Validator(schema_root)

    def _prepare_scenarios(self, scenario_cfg: Sequence[Dict[str, Any]]) -> List[ScenarioSpec]:
        specs: List[ScenarioSpec] = []
        for raw in scenario_cfg:
            fields: Dict[str, Dict[str, Any]] = {}
            options: Dict[str, Dict[str, Any]] = {}
            for key, value in raw.get("campos", {}).items():
                if isinstance(value, dict) and {"fixo", "opcoes"} & value.keys():
                    fields[key] = value
                else:
                    options[key] = value if isinstance(value, dict) else {"valor": value}
            specs.append(
                ScenarioSpec(
                    name=raw["nome"],
                    weight=float(raw.get("peso", 0.0)),
                    volume=raw.get("volume"),
                    profile=raw.get("perfil_monetario", "padrao"),
                    field_specs=fields,
                    options=options,
                )
            )
        return specs

    def _create_user_pool(self, num_usuarios: int) -> List[Usuario]:
        usuarios: List[Usuario] = []
        for _ in range(num_usuarios):
            billing = self._generate_address_for_country("076")
            usuario = Usuario(
                cardHolderDocument=self._generate_numeric_string(11),
                cardholderName=self._truncate(self.fakers["pt_BR"].name(), 45),
                acctNumber=self._generate_numeric_string(self.rng.integers(13, 20), allow_leading_zero=False),
                cardExpiryDate=self._generate_card_expiry(),
                email=self.fakers["pt_BR"].email(),
                billAddrLine1=billing["line1"],
                billAddrLine2=billing["line2"],
                billAddrCity=billing["city"],
                billAddrState=billing["state"],
                billAddrCountry=billing["country"],
                billAddrPostCode=billing["postcode"],
            )
            usuarios.append(usuario)
        return usuarios

    def generate(self, total_override: Optional[int] = None) -> List[Dict[str, Any]]:
        total = total_override or int(self.config["geracao"]["volume_total"])
        usuarios_cfg = self.config["geracao"].get("usuarios", {})
        trans_min = int(usuarios_cfg.get("transacoes_min", 10))
        trans_max = int(usuarios_cfg.get("transacoes_max", 30))
        
        num_usuarios = max(1, total // ((trans_min + trans_max) // 2))
        usuarios = self._create_user_pool(num_usuarios)
        
        allocations = self._scenario_volumes(total)
        registros: List[Dict[str, Any]] = []
        
        for scenario, volume in allocations:
            for _ in range(volume):
                usuario = usuarios[int(self.rng.integers(0, len(usuarios)))]
                registro = self._build_record_for_scenario(scenario, usuario)
                registros.append(registro)
        
        self._validate_records(registros)
        return registros

    def validate_records(self, records: Sequence[Dict[str, Any]]) -> None:
        self._validate_records(records)

    def _scenario_volumes(self, total: int) -> List[tuple[ScenarioSpec, int]]:
        allocations: List[tuple[ScenarioSpec, int]] = []
        remaining = total
        variable_specs: List[ScenarioSpec] = []
        for scenario in self.scenarios:
            if scenario.volume:
                count = min(int(scenario.volume), remaining)
                allocations.append((scenario, count))
                remaining -= count
            else:
                variable_specs.append(scenario)
        if variable_specs and remaining > 0:
            weights = np.array([spec.weight for spec in variable_specs], dtype=float)
            if np.isclose(weights.sum(), 0.0):
                weights[:] = 1.0 / len(variable_specs)
            else:
                weights = weights / weights.sum()
            allocated = self.rng.multinomial(remaining, weights)
            for spec, count in zip(variable_specs, allocated):
                if count:
                    allocations.append((spec, int(count)))
        return allocations

    def _build_record_for_scenario(self, scenario: ScenarioSpec, usuario: Usuario) -> Dict[str, Any]:
        record: Dict[str, Any] = {}
        self._apply_common_fields(record)
        self._inject_dynamic_defaults(record, usuario)
        self._apply_scenario_fields(record, scenario.field_specs)
        self._finalize_amounts(record, scenario.profile)
        self._apply_scenario_options(record, scenario)
        self._assign_label(record, scenario.name)
        self._populate_lifecycle_fields(record)
        self._populate_addresses(record, scenario.name, usuario)
        self._ensure_required_fields(record)
        return record

    def _apply_common_fields(self, record: Dict[str, Any]) -> None:
        for field, spec in self.common_fields.items():
            record[field] = self._resolve_spec_value(spec)

    def _inject_dynamic_defaults(self, record: Dict[str, Any], usuario: Usuario) -> None:
        record.setdefault("messageExtension", [])
        record["threeDSServerTransID"] = str(uuid4())
        record["purchaseDate"] = self._format_datetime(self._random_recent_datetime())
        record["browserScreenHeight"] = str(self.rng.integers(640, 1600))
        record["browserScreenWidth"] = str(self.rng.integers(960, 2560))
        record["browserIP"] = self.fakers["pt_BR"].ipv4_public()
        record["browserUserAgent"] = self.fakers["pt_BR"].user_agent()
        record["cardholderName"] = usuario.cardholderName
        record["acctNumber"] = usuario.acctNumber
        record["cardExpiryDate"] = usuario.cardExpiryDate
        record["cardHolderDocument"] = usuario.cardHolderDocument
        record["cardSecurityCode"] = self._generate_numeric_string(3)
        record["email"] = usuario.email
        record["merchantName"] = self._truncate(self.fakers["pt_BR"].company(), 40)
        record["merchantDocument"] = self._generate_numeric_string(14)
        record["purchaseInstalData"] = self._resolve_spec_value(self.common_fields.get("purchaseInstalData", {"fixo": "01"}))
        record["browserLanguage"] = record.get(
            "browserLanguage", self._resolve_spec_value(self.common_fields.get("browserLanguage", {"fixo": "pt-BR"}))
        )

    def _apply_scenario_fields(self, record: Dict[str, Any], field_specs: Dict[str, Dict[str, Any]]) -> None:
        for name, spec in field_specs.items():
            value = self._resolve_spec_value(spec)
            self._set_nested(record, name, value)

    def _apply_scenario_options(self, record: Dict[str, Any], scenario: ScenarioSpec) -> None:
        if "multiTransaction" in scenario.options:
            self._populate_marketplace_details(record, scenario.options["multiTransaction"])
        if "sellerInfo" in scenario.options:
            self._populate_seller_info(record, scenario.options["sellerInfo"])

    def _finalize_amounts(self, record: Dict[str, Any], profile: str) -> None:
        exponent = int(record.get("purchaseExponent", "2"))
        amount = self._sample_amount(profile, exponent)
        record["purchaseAmount"] = amount
        if record.get("deviceChannel") == "01":
            record.setdefault("sdkTransID", str(uuid4()))
        if record.get("payTokenInd"):
            record["payTokenInfo"] = self._build_pay_token_info()
        if record.get("threeRIInd"):
            self._build_recurring_fields(record)

    def _populate_lifecycle_fields(self, record: Dict[str, Any]) -> None:
        record.setdefault("transStatus", "Y")
        record.setdefault("eci", "05")
        if record["transStatus"] == "N" and "transStatusReason" not in record:
            record["transStatusReason"] = "01"

    def _populate_addresses(self, record: Dict[str, Any], scenario_name: str, usuario: Usuario) -> None:
        record.update({
            "billAddrLine1": usuario.billAddrLine1,
            "billAddrLine2": usuario.billAddrLine2,
            "billAddrLine3": "",
            "billAddrCity": usuario.billAddrCity,
            "billAddrState": usuario.billAddrState,
            "billAddrCountry": usuario.billAddrCountry,
            "billAddrPostCode": usuario.billAddrPostCode,
        })
        
        ship_same = scenario_name not in {"transacao_negada", "marketplace"} or self.rng.random() > 0.5
        if ship_same:
            record.update({
                "shipAddrLine1": record["billAddrLine1"],
                "shipAddrLine2": "",
                "shipAddrLine3": "",
                "shipAddrCity": record["billAddrCity"],
                "shipAddrState": record["billAddrState"],
                "shipAddrCountry": record["billAddrCountry"],
                "shipAddrPostCode": record["billAddrPostCode"],
                "addrMatch": "Y",
            })
        else:
            shipping = self._generate_address_for_country(self._select_alternate_country(usuario.billAddrCountry))
            record.update({
                "shipAddrLine1": shipping["line1"],
                "shipAddrLine2": shipping["line2"],
                "shipAddrLine3": "",
                "shipAddrCity": shipping["city"],
                "shipAddrState": shipping["state"],
                "shipAddrCountry": shipping["country"],
                "shipAddrPostCode": shipping["postcode"],
                "addrMatch": "N",
            })

    def _ensure_required_fields(self, record: Dict[str, Any]) -> None:
        for field in self.required_fields:
            if "." in field:
                continue
            if field not in record:
                record[field] = ""

    def _populate_marketplace_details(self, record: Dict[str, Any], settings: Dict[str, Any]) -> None:
        itens_min = int(settings.get("itens_min", 2))
        itens_max = int(settings.get("itens_max", 3))
        itens = int(self.rng.integers(itens_min, itens_max + 1))
        exponent = int(record.get("purchaseExponent", "2"))
        total = int(record["purchaseAmount"])
        parts = self._split_amount(total, itens)
        merchant_currency = record.get("purchaseCurrency", "986")
        merchant_list = []
        for part in parts:
            merchant_list.append({
                "merchantNameListed": self._truncate(self.fakers["pt_BR"].company(), 40),
                "acquirerMerchantIdListed": self._generate_numeric_string(15),
                "merchantAmount": str(part),
                "merchantCurrency": merchant_currency,
                "merchantExponent": str(exponent),
                "sellerId": str(uuid4())[:36],
            })
        record["multiTransaction"] = {
            "avNumberUse": "01",
            "avValidityTime": "060",
            "merchantList": merchant_list,
        }

    def _populate_seller_info(self, record: Dict[str, Any], settings: Dict[str, Any]) -> None:
        min_sellers = int(settings.get("vendedores_min", 1))
        max_sellers = int(settings.get("vendedores_max", 3))
        count = int(self.rng.integers(min_sellers, max_sellers + 1))
        sellers: List[Dict[str, Any]] = []
        for _ in range(count):
            sellers.append(self._build_seller_entry())
        record["sellerInfo"] = sellers

    def _build_pay_token_info(self) -> Dict[str, Any]:
        return {
            "token": self._generate_numeric_string(self.rng.integers(16, 20)),
            "tokenAdditionalData": json.dumps({"deviceBinding": "ON"}),
            "tokenAssuranceMethod": "01",
            "tokenCryptogram": self.fakers["en_US"].md5(raw_output=False),
            "tokenCryptogramValidityIndicator": "01",
            "tokenRequestorId": self._generate_numeric_string(11),
            "tokenStatusIndicator": "ACTIVE",
        }

    def _build_recurring_fields(self, record: Dict[str, Any]) -> None:
        exponent = int(record.get("purchaseExponent", "2"))
        settings = self.monetary_profiles.get("recorrencia", self.monetary_profiles.get("padrao", {}))
        amount = self._sample_amount("recorrencia", exponent, fallback=settings)
        record["recurringAmount"] = amount
        record["recurringCurrency"] = record.get("purchaseCurrency", "986")
        base_date = datetime.now(UTC)
        record["recurringDate"] = (base_date + timedelta(days=30)).strftime("%Y%m%d")
        record["recurringExpiry"] = (base_date + timedelta(days=360)).strftime("%Y%m%d")
        record["recurringFrequency"] = "30"
        record["paymentInfo"] = {
            "cofDate": base_date.isoformat(),
            "cofNumber": int(self.rng.integers(1, 10)),
            "cofNumber24h": int(self.rng.integers(0, 4)),
            "cofNumber7d": int(self.rng.integers(1, 15)),
            "creationDate": base_date.isoformat(),
            "updateDate": base_date.isoformat(),
        }

    def _build_seller_entry(self) -> Dict[str, Any]:
        seller_faker = self.fakers["pt_BR"]
        seller_addr = self._generate_address_for_country("076")
        return {
            "sellerAccDate": (datetime.now(UTC) - timedelta(days=int(self.rng.integers(60, 720)))).strftime("%Y%m%d"),
            "sellerAddrCity": seller_addr["city"],
            "sellerAddrCountry": seller_addr["country"],
            "sellerAddrLine1": seller_addr["line1"],
            "sellerAddrLine2": seller_addr["line2"],
            "sellerAddrLine3": "",
            "sellerAddrPostCode": seller_addr["postcode"],
            "sellerAddrState": seller_addr["state"],
            "sellerBusinessName": self._truncate(seller_faker.company(), 100),
            "sellerDocument": self._generate_numeric_string(14),
            "sellerEmail": seller_faker.company_email(),
            "sellerId": str(uuid4())[:36],
            "sellerName": self._truncate(seller_faker.name(), 100),
            "sellerPhone": {
                "cc": "55",
                "subscriber": self._generate_numeric_string(9),
            },
        }

    def _validate_records(self, records: Sequence[Dict[str, Any]]) -> None:
        errors: List[str] = []
        for idx, record in enumerate(records):
            try:
                self.validator.validate(record)
            except ValidationError as exc:
                errors.append(f"Registro {idx}: {exc.message}")
            if len(errors) >= 5:
                break
        if errors:
            raise ValueError("Falha na validação dos registros sintéticos:\n" + "\n".join(errors))

    def _resolve_spec_value(self, spec: Dict[str, Any]) -> Any:
        if "fixo" in spec:
            return spec["fixo"]
        if "opcoes" in spec:
            return self._weighted_choice(spec["opcoes"])
        raise ValueError(f"Especificação desconhecida: {spec}")

    def _weighted_choice(self, options: Sequence[Dict[str, Any]]) -> Any:
        valores = [item["valor"] for item in options]
        pesos = np.array([float(item.get("peso", 1.0)) for item in options], dtype=float)
        if pesos.sum() <= 0:
            pesos = np.ones_like(pesos) / len(pesos)
        else:
            pesos = pesos / pesos.sum()
        indice = int(self.rng.choice(len(valores), p=pesos))
        return valores[indice]

    def _set_nested(self, record: Dict[str, Any], dotted_key: str, value: Any) -> None:
        parts = dotted_key.split(".")
        target = record
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    def _assign_label(self, record: Dict[str, Any], scenario_name: str) -> None:
        if not self.label_field:
            return
        prob = self.label_probs.get(scenario_name, self.label_default_prob)
        prob = min(max(prob, 0.0), 1.0)
        value = 1 if self.rng.random() < prob else 0
        if self.label_format == "bool":
            record[self.label_field] = bool(value)
        elif self.label_format == "str":
            record[self.label_field] = str(value)
        else:
            record[self.label_field] = int(value)

    def _sample_amount(self, profile: str, exponent: int, fallback: Optional[Dict[str, Any]] = None) -> str:
        settings = self.monetary_profiles.get(profile) or fallback or self.monetary_profiles.get("padrao", {})
        media = float(settings.get("media", 200.0))
        desvio = float(settings.get("desvio", 80.0))
        minimo = float(settings.get("minimo", 5.0))
        maximo = float(settings.get("maximo", 10000.0))
        valor = self.rng.normal(media, desvio)
        valor = max(min(valor, maximo), minimo)
        inteiro = max(int(round(valor * (10**exponent))), 1)
        return str(inteiro)

    def _split_amount(self, total: int, parts: int) -> List[int]:
        if parts <= 1:
            return [total]
        pesos = self.rng.random(parts)
        pesos = pesos / pesos.sum()
        valores = (pesos * total).astype(int)
        diferenca = total - valores.sum()
        for _ in range(abs(diferenca)):
            idx = int(self.rng.integers(0, parts))
            valores[idx] += 1 if diferenca > 0 else -1
        ajustado = [max(int(v), 1) for v in valores]
        ajuste_final = total - sum(ajustado)
        if ajuste_final != 0:
            idx = int(self.rng.integers(0, parts))
            novo_valor = ajustado[idx] + ajuste_final
            ajustado[idx] = max(novo_valor, 1)
            diferenca_pos = total - sum(ajustado)
            if diferenca_pos != 0:
                ajustado[0] = max(ajustado[0] + diferenca_pos, 1)
        return ajustado

    def _random_recent_datetime(self) -> datetime:
        offset = int(self.rng.integers(0, 30 * 24 * 60 * 60))
        return datetime.now(UTC) - timedelta(seconds=offset)

    def _format_datetime(self, value: datetime) -> str:
        return value.strftime("%Y%m%d%H%M%S")

    def _generate_card_expiry(self) -> str:
        months_ahead = int(self.rng.integers(6, 60))
        future = datetime.now(UTC) + timedelta(days=30 * months_ahead)
        return future.strftime("%y%m")

    def _generate_numeric_string(self, length: int, allow_leading_zero: bool = True) -> str:
        digits = []
        for idx in range(length):
            if idx == 0 and not allow_leading_zero:
                digit = str(self.rng.integers(1, 10))
            else:
                digit = str(self.rng.integers(0, 10))
            digits.append(digit)
        return "".join(digits)

    def _truncate(self, value: str, max_length: int) -> str:
        return value[:max_length]

    def _select_alternate_country(self, current: str) -> str:
        available = [code for code in COUNTRY_PROFILES if code != current]
        if not available:
            return current
        return available[int(self.rng.integers(0, len(available)))]

    def _generate_address_for_country(self, country_code: str) -> Dict[str, str]:
        profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["076"])
        faker = self.fakers[profile["locale"]]
        line1 = self._truncate(faker.street_address(), 50)
        city = self._truncate(faker.city(), 50)
        state_value = ""
        for attr in ("state_abbr", "estado_sigla", "state", "administrative_unit"):
            if hasattr(faker, attr):
                try:
                    state_value = getattr(faker, attr)()
                except TypeError:
                    continue
                if state_value:
                    break
        state = self._truncate(state_value or "", 3)
        postcode = "".join(filter(str.isalnum, faker.postcode()))[:16]
        return {
            "line1": line1,
            "line2": "",
            "city": city,
            "state": state,
            "country": country_code,
            "postcode": postcode,
        }


def write_outputs(records: Sequence[Dict[str, Any]], output_dir: Path, output_cfg: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    csv_path = output_dir / output_cfg.get("csv", "dataset_sintetico.csv")
    jsonl_path = output_dir / output_cfg.get("jsonl", "payloads_sinteticos.jsonl")
    df.to_csv(csv_path, index=False)
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    
    print(f"\nGerados {len(records)} registros")
    print(f"Usuarios unicos: {df['cardHolderDocument'].nunique()}")
    print(f"Transacoes por usuario: {len(records) / df['cardHolderDocument'].nunique():.1f} (media)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerador de base sintética para Online Purchase")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("configuracoes_cenarios.yaml"),
        help="Caminho para o arquivo de configuração YAML",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=None,
        help="Sobrescreve o volume total definido no YAML",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path(__file__).parent,
        help="Diretório de saída para CSV e JSONL",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    generator = SyntheticPurchaseGenerator(config=config, config_path=args.config)
    registros = generator.generate(total_override=args.volume)
    write_outputs(registros, args.saida, config["geracao"]["output"])


if __name__ == "__main__":
    main()

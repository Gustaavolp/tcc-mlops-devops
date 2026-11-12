"""Testes da normalização do payload 3DS para o formato esperado pelo modelo."""
import pytest

from classes.normalize_payload import PayloadNormalizer


@pytest.fixture
def normalizer():
    return PayloadNormalizer()


def test_mapeia_campos_do_payload_para_colunas_do_modelo(normalizer):
    out = normalizer.normalize_request({
        "purchaseAmount": "150.75",
        "purchaseCurrency": " 986 ",
        "mcc": "5411",
        "acctID": "abc123",
    })
    assert out["AMOUNT"] == 150.75
    assert out["CURRENCY"] == "986"            # string com espaços é aparada
    assert out["MERCHANT_CATEGORY_CODE"] == "5411"
    assert out["CARDHOLDER_ACCOUNT_IDENTIFIER"] == "abc123"


@pytest.mark.parametrize("raw,expected", [
    ("Y", True), ("true", True), ("1", True), ("sim", True),
    ("N", False), ("false", False), ("0", False), ("não", False),
    ("talvez", None), (None, None), ("", None),
])
def test_normaliza_booleanos(normalizer, raw, expected):
    assert normalizer._normalize_bool(raw) is expected


@pytest.mark.parametrize("raw,expected", [("10", 10.0), ("abc", 0.0), (None, 0.0), ("", 0.0)])
def test_valores_numericos_invalidos_viram_zero(normalizer, raw, expected):
    assert normalizer._normalize_double(raw) == expected


def test_campos_ausentes_nao_quebram_e_tem_valor_padrao(normalizer):
    out = normalizer.normalize_request({})
    assert out["AMOUNT"] == 0.0
    assert out["BROWSER_LANGUAGE"] is None
    assert out["ADDR_MATCH_INDICATOR"] is None
    # todas as colunas de treino estão presentes na saída
    assert set(normalizer.trained_columns) <= set(out)


def test_get_value_navega_chaves_aninhadas(normalizer):
    payload = {"acctInfo": {"shipNameIndicator": "01"}}
    assert normalizer._get_value(payload, "acctInfo.shipNameIndicator") == "01"
    assert normalizer._get_value(payload, "acctInfo.inexistente") is None
    assert normalizer._get_value({"a": "texto"}, "a.b") is None

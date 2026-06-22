import json
import re
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

class PayloadNormalizer:
    def __init__(self):
        self.trained_columns = [
            "ACCT_TYPE", "ACQUIRER_BIN", "ADDR_MATCH_INDICATOR",
            "CARDHOLDER_BILL_ADDR_COUNTRY", "CARDHOLDER_BILL_ADDR_STATE",
            "BROWSER_JAVA_ENABLED", "BROWSER_JAVASCRIPT_ENABLED",
            "BROWSER_LANGUAGE", "BROWSER_TIME_ZONE", "DEVICE_CHANNEL",
            "MERCHANT_CATEGORY_CODE", "MERCHANT_COUNTRY", "MESSAGE_CATEGORY",
            "AMOUNT", "CURRENCY", "INSTALMENT_PAYMENT_DATA",
            "CARDHOLDER_SHIP_ADDR_COUNTRY", "3DS_REQ_AUTH_IND",
            "3DS_REQ_CHALLENGE_IND", "3DS_METHOD_COMPLETION_IND",
            "3DS_SERVER_OPER_ID", "TRANSACTION_TYPE"
        ]

        self.list_string = [
            "TRANSACTION_TYPE", "CARDHOLDER_BILL_ADDR_COUNTRY", "CARDHOLDER_BILL_ADDR_STATE",
            "CARDHOLDER_SHIP_ADDR_COUNTRY", "ACCT_TYPE", "CURRENCY", "ACQUIRER_BIN",
            "MERCHANT_COUNTRY", "MERCHANT_CATEGORY_CODE", "3DS_REQ_AUTH_IND",
            "3DS_REQ_CHALLENGE_IND", "3DS_SERVER_OPER_ID", "3DS_METHOD_COMPLETION_IND",
            "BROWSER_LANGUAGE", "BROWSER_TIME_ZONE"
        ]
        self.list_bool = [
            "BROWSER_JAVA_ENABLED", "BROWSER_JAVASCRIPT_ENABLED", "ADDR_MATCH_INDICATOR"
        ]
        self.list_double = [
            "DEVICE_CHANNEL", "MESSAGE_CATEGORY", "AMOUNT", "INSTALMENT_PAYMENT_DATA"
        ]

        self.mapping = {
            "ACCT_TYPE": "acctType",
            "ACQUIRER_BIN": "acquirerBIN",
            "ADDR_MATCH_INDICATOR": "addrMatch",
            "CARDHOLDER_BILL_ADDR_COUNTRY": "billAddrCountry",
            "CARDHOLDER_BILL_ADDR_STATE": "billAddrState",
            "BROWSER_JAVA_ENABLED": "browserJavaEnabled",
            "BROWSER_JAVASCRIPT_ENABLED": "browserJavascriptEnabled",
            "BROWSER_LANGUAGE": "browserLanguage",
            "BROWSER_TIME_ZONE": "browserTZ",
            "DEVICE_CHANNEL": "deviceChannel",
            "MERCHANT_CATEGORY_CODE": "mcc",
            "MERCHANT_COUNTRY": "merchantCountryCode",
            "MESSAGE_CATEGORY": "messageCategory",
            "AMOUNT": "purchaseAmount",
            "CURRENCY": "purchaseCurrency",
            "INSTALMENT_PAYMENT_DATA": "purchaseInstalData",
            "CARDHOLDER_SHIP_ADDR_COUNTRY": "shipAddrCountry",
            "3DS_REQ_AUTH_IND": "threeDSRequestorAuthenticationInd",
            "3DS_REQ_CHALLENGE_IND": "threeDSRequestorChallengeInd",
            "3DS_METHOD_COMPLETION_IND": "threeDSRequestorDecReqInd",
            "3DS_SERVER_OPER_ID": "threeDSServerOperatorID",
            "TRANSACTION_TYPE": "transType",
            
            # Campos Extras necessários para Feature Store ou Identificação
            "PURCHASE_DATE_AND_TIME": "purchaseDate",
            "BROWSER_USER_AGENT": "browserUserAgent",
            "CARDHOLDER_BILL_ADDR_CITY": "billAddrCity",
            "CARDHOLDER_SHIP_ADDR_CITY": "shipAddrCity",
            "MERCHANT_ID": "acquirerMerchantID",
            "CARDHOLDER_ACCOUNT_IDENTIFIER": "acctID",
            "cardHolderDocument": "cardHolderDocument"
        }

    def _get_value(self, payload: Dict[str, Any], path: str) -> Any:
        """Navega por chaves aninhadas (ex: acctInfo.shipNameIndicator)"""
        if not path: return None
        keys = path.split('.')
        curr = payload
        try:
            for k in keys:
                if isinstance(curr, dict):
                    curr = curr.get(k)
                else:
                    return None
            return curr
        except:
            return None

    def _normalize_string(self, x: Any) -> Optional[str]:
        if x is None: return None
        s = str(x).strip()
        return s if s != "" else None

    def _normalize_bool(self, x: Any) -> Optional[bool]:
        s = self._normalize_string(x)
        if s is None: return None
        s = s.lower()
        if s in {"y", "yes", "s", "sim", "true", "1"}: return True
        if s in {"n", "no", "nao", "não", "false", "0"}: return False
        return None

    def _normalize_double(self, x: Any) -> float:
        try:
            if x is None or str(x).strip() == "": return 0.0
            return float(x)
        except:
            return 0.0

    def _parse_date(self, x: Any) -> Optional[str]:
        if not x: return None
        s = str(x).strip()
        return s

    def normalize_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}

        all_keys = set(self.trained_columns) | set(self.mapping.keys())
        
        for col in all_keys:
            path = self.mapping.get(col)
            if not path:
                continue

            raw_val = self._get_value(payload, path)

            if col in self.list_string:
                normalized[col] = self._normalize_string(raw_val)
            elif col in self.list_bool:
                normalized[col] = self._normalize_bool(raw_val)
            elif col in self.list_double:
                normalized[col] = self._normalize_double(raw_val)
            elif col == "PURCHASE_DATE_AND_TIME":
                normalized[col] = self._parse_date(raw_val)
            else:
                normalized[col] = raw_val

        return normalized
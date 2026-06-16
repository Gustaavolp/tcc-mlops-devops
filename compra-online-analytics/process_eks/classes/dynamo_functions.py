import boto3
import json
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

class DynamoEventTable:
    def __init__(self, table_name, region="us-east-1"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        
    def parse_iso_timestamp(self, ts):
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except:
            return datetime.now()

    def extract_timestamp(self, item):
        try:
            # Se já for numérico (Decimal/int/float) no banco
            if "timestamp" in item:
                val = item["timestamp"]
                if isinstance(val, (int, float, Decimal)):
                    return datetime.fromtimestamp(float(val))
                return self.parse_iso_timestamp(val)
            
            # Se estiver dentro do payload JSON
            if "payload" in item:
                p = item["payload"]
                payload_dict = json.loads(p) if isinstance(p, str) else p
                
                ts_str = payload_dict.get("PURCHASE_DATE_AND_TIME")
                
                if ts_str:
                    # Tenta numérico primeiro
                    try:
                        return datetime.fromtimestamp(float(ts_str))
                    except:
                        return self.parse_iso_timestamp(ts_str)
        except:
            pass
        return datetime.min

    def get_events_by_acctID(self, acctID):
        try:
            response = self.table.query(
                KeyConditionExpression=Key("acctID").eq(str(acctID))
            )
            return response.get("Items", [])
        except ClientError as e:
            print(f"Erro no QUERY: {e}")
            return []

    def save_event(self, acctID, threeDSServerTransID, payload_dict, n_keep=15):
        try:            
            # 1. Trata o Transaction ID

            tx_id_db = str(threeDSServerTransID)

            # 2. Trata o Timestamp (O causador do erro "Float types are not supported")
            raw_ts = payload_dict.get("PURCHASE_DATE_AND_TIME") or datetime.now().timestamp()
            
            # Se for float (ex: time.time()), converte para Decimal
            if isinstance(raw_ts, float):
                timestamp_val = Decimal(str(raw_ts))
            else:
                # Se for string ISO, mantém string
                timestamp_val = str(raw_ts)

            # Prepara o JSON do payload
            # (json.dumps converte floats internos para string no JSON, então aqui é seguro)
            payload_json = json.dumps(payload_dict, default=str)

            # --- LÓGICA DE BANCO ---

            # 1. Busca histórico existente
            events = self.get_events_by_acctID(acctID)
            
            # 2. Idempotência (Update se já existe)
            for e in events:
                # Compara strings ou decimals de forma segura
                if str(e.get('threeDSServerTransID')) == str(tx_id_db):
                    self.table.update_item(
                        Key={
                            "acctID": str(acctID), 
                            "threeDSServerTransID": tx_id_db
                        },
                        UpdateExpression="SET payload = :p, #ts = :t",
                        ExpressionAttributeNames={"#ts": "timestamp"},
                        ExpressionAttributeValues={
                            ":p": payload_json, 
                            ":t": timestamp_val 
                        }
                    )
                    return True

            # 3. Rotação (Deleta antigos)
            if len(events) >= n_keep:
                # Ordena pelo timestamp extraído
                events_sorted = sorted(events, key=lambda ev: self.extract_timestamp(ev))
                qtd_remover = len(events) - n_keep + 1
                
                for i in range(qtd_remover):
                    oldest = events_sorted[i]
                    self.table.delete_item(
                        Key={
                            "acctID": oldest["acctID"],
                            "threeDSServerTransID": oldest["threeDSServerTransID"]
                        }
                    )

            # 4. Inserir Novo Item
            item = {
                "acctID": str(acctID),
                "threeDSServerTransID": tx_id_db,
                "timestamp": timestamp_val,
                "payload": payload_json
            }
            
            self.table.put_item(Item=item)
            return True

        except Exception as e:
            print(f"Erro crítico DynamoDB (save_event): {e}")
            return None
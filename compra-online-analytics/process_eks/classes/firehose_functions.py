import boto3
import json

class FirehoseClient:
    def __init__(self, stream_name, region="us-east-1"):
        self.client = boto3.client("firehose", region_name=region)
        self.stream_name = stream_name

    def put_record(self, data_dict):
        try:
            # Firehose espera bytes e uma quebra de linha para arquivos JSON Lines
            data_str = json.dumps(data_dict, default=str) + "\n"
            
            response = self.client.put_record(
                DeliveryStreamName=self.stream_name,
                Record={'Data': data_str.encode('utf-8')}
            )
            print(f"Enviado para Firehose: {response['RecordId']}")
            return response
        except Exception as e:
            print(f"Erro no Firehose: {e}")
            return None
    
    def put_records_batch(self, data_list):
        """
        Envia toda a lista de JSONs de uma vez, sem for, usando put_record_batch.
        Limite: até 500 registros por batch.
        Aceita qualquer iterável, tentando converter para lista.
        """

        print(data_list)
        # Tenta converter para lista
        if isinstance(data_list, str):        
            try:
                data_list = json.loads(data_list)
            except TypeError:
                raise TypeError("data_list deve ser um json, não string")

        if not data_list:
            return None

        if len(data_list) > 500:
            raise ValueError("put_record_batch suporta no máximo 500 registros por chamada")

        # Converte toda a lista de dicionários em registros para Firehose
        records = list(map(lambda d: {'Data': (json.dumps(d, default=str) + "\n").encode('utf-8')}, data_list))

        response = self.client.put_record_batch(
            DeliveryStreamName=self.stream_name,
            Records=records
        )

        print(f"Lote enviado: {len(records)} registros, FailedCount: {response['FailedPutCount']}")
        return response
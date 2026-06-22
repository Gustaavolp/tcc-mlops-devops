import json

def build_bedrock_response(action_group, api_path, http_method, status_code, body_dict,
                           session_attributes, prompt_session_attributes):
    """
    Constrói a resposta no formato esperado pelo Bedrock Agents.
    O body é serializado em string JSON dentro de responseBody.application/json.body.
    """
    response_body = {
        "application/json": {
            "body": json.dumps(body_dict)
        }
    }
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status_code,
            "responseBody": response_body
        },
        "sessionAttributes": session_attributes,
        "promptSessionAttributes": prompt_session_attributes
    }
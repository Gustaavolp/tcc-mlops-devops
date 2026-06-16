from best_model_register import MlflowModelRegistry

def lambda_handler(event, context):

    registry = MlflowModelRegistry()
    status = registry.register_best_model()

    return status

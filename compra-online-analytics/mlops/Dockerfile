FROM public.ecr.aws/lambda/python:3.12

# Requirements copy and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy function code
COPY best_model_register.py ${LAMBDA_TASK_ROOT}/
COPY envs.py ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY utils.py ${LAMBDA_TASK_ROOT}/

# Handler
CMD ["lambda_handler.lambda_handler"]
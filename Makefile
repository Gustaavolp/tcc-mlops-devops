.PHONY: help install install-dev format lint test test-images test-pipelines clean

help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Static analysis used by the CI/CD pipelines (ruff, ruff.toml)"
	@echo "  test         - Run tests with coverage"
	@echo "  test-images  - Build each container image and run its pytest suite inside it (A=<artifact> for one)"
	@echo "  test-pipelines - Test CI/CD scripts (stubs) and the infra/cicd Terraform stack (terraform test)"
	@echo "  clean        - Remove build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

format:
	black .
	isort .

lint:
	ruff check --config ruff.toml services lambdas models/sagemaker_training pipelines

test:
	pytest

test-images:
	bash pipelines/scripts/run_local.sh $(A)

test-pipelines:
	bash pipelines/tests/test_scripts.sh
	terraform -chdir=infra/cicd init -backend=false -input=false >/dev/null
	terraform -chdir=infra/cicd test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage

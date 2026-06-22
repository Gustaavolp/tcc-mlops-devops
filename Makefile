.PHONY: help install install-dev format lint test clean

help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run linters (flake8, mypy)"
	@echo "  test         - Run tests with coverage"
	@echo "  clean        - Remove build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

format:
	black .
	isort .

lint:
	flake8 services/ mlops/
	mypy services/ mlops/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage

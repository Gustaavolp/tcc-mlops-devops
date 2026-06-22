"""
Feature engineering blueprint package for fraud scoring.

This package contains a minimal, dependency-free blueprint to transform
the incoming request payload (as defined in schemas/fraud_scoring_request.schema.json)
into a feature dictionary suitable for model inference/training.
"""

from .blueprint import FeatureExtractor, Enricher, FeatureStoreClient  # noqa: F401


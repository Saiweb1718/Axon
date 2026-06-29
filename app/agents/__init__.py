"""Importing this package registers every agent in the shared REGISTRY.

Adding a new agent = drop a module here and `register(...)` it. The planner
discovers it automatically via the manifest — no engine change required.
"""
from . import analyzer, execution, explainer, ingestion, recommender, retrieval  # noqa: F401

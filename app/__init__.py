"""Axon — a reusable Agentic Decision Intelligence Platform.

The engine is domain-agnostic. The Customer Success use case lives entirely in
`config/` and `data/` — swap those to point the same engine at a new domain.
"""

# Load .env (GEMINI_API_KEY, LLM_PROVIDER, LANGFUSE_*, …) before anything reads env.
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv()
except Exception:  # python-dotenv optional; the host may set env vars directly
    pass


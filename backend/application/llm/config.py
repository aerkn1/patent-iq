from __future__ import annotations

SNAPSHOT_DATE_FIXED_V1 = "2025-01-31"

GROQ_MODEL_DEFAULT = "llama-3.1-8b-instant"
GROQ_MODEL_FALLBACK = "llama-3.3-70b-versatile"

# Conservative caps; can be tuned per endpoint.
MAX_TOKENS_PORTFOLIO = 1400
MAX_TOKENS_PATENT = 1200
MAX_TOKENS_PORTFOLIO_EVOLUTION = 1600

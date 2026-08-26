from functools import lru_cache

from app.config import settings
from app.llm.base import LLMAdapter, LLMAdapterError


@lru_cache(maxsize=1)
def get_llm_adapter() -> LLMAdapter:
    """Return the configured LLM adapter, chosen by LLM_PROVIDER.

    This is the ONLY supported way to get an LLM adapter — call sites
    must never import a provider class (e.g. OllamaAdapter) directly.
    Adding a new provider means adding one branch here plus its own
    module in this package; nothing else in the codebase changes.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from app.llm.groq_adapter import GroqAdapter

        return GroqAdapter(model=settings.LLM_MODEL, api_key=settings.GROQ_API_KEY)

    if provider == "ollama":
        from app.llm.ollama_adapter import OllamaAdapter

        return OllamaAdapter(model=settings.LLM_MODEL, base_url=settings.OLLAMA_BASE_URL)

    raise LLMAdapterError(
        f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. Supported providers: groq, ollama."
    )

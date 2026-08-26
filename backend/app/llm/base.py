from abc import ABC, abstractmethod
from typing import Optional


class LLMAdapterError(Exception):
    """Raised when the configured LLM backend can't fulfill a request.

    Callers should be able to show `str(exc)` directly to a user/developer
    without leaking a raw stack trace.
    """


class LLMAdapter(ABC):
    """Minimal, model-agnostic interface for text generation.

    Every LLM-backed feature in this codebase must call an implementation
    of this interface via `app.llm.get_llm_adapter()` — never a specific
    provider class directly. That's what makes swapping Ollama for Groq,
    OpenAI, etc. later a one-file change instead of a codebase-wide hunt.
    """

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a text completion for `prompt`.

        `system` is an optional system-level instruction (persona, output
        format constraints, etc.) separate from the user-facing prompt.
        Returns the generated text with leading/trailing whitespace stripped.
        """
        raise NotImplementedError

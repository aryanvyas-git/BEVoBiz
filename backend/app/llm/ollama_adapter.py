from typing import Optional

import ollama

from app.llm.base import LLMAdapter, LLMAdapterError


class OllamaAdapter(LLMAdapter):
    """Talks to a locally running Ollama server via its HTTP API.

    Not meant to be imported outside of `app.llm.factory` — get an
    instance via `app.llm.get_llm_adapter()` instead.
    """

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url
        self._client = ollama.Client(host=base_url)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            response = self._client.generate(
                model=self.model, prompt=prompt, system=system, stream=False
            )
        except ConnectionError as exc:
            raise LLMAdapterError(
                f"Could not reach Ollama at {self.base_url}. "
                "Start it first (run `ollama serve`, or open the Ollama app), then try again."
            ) from exc
        except ollama.ResponseError as exc:
            if exc.status_code == 404 or "not found" in str(exc.error).lower():
                raise LLMAdapterError(
                    f"Model '{self.model}' isn't available on this Ollama server yet. "
                    f"Pull it first with `ollama pull {self.model}`."
                ) from exc
            raise LLMAdapterError(f"Ollama request failed: {exc.error}") from exc
        except Exception as exc:
            raise LLMAdapterError(f"Unexpected error talking to Ollama: {exc}") from exc

        return (response.response or "").strip()

from typing import Optional

import groq

from app.llm.base import LLMAdapter, LLMAdapterError


class GroqAdapter(LLMAdapter):
    """Talks to Groq's hosted, OpenAI-compatible chat completions API.

    Not meant to be imported outside of `app.llm.factory` — get an
    instance via `app.llm.get_llm_adapter()` instead.
    """

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self._client = groq.Groq(api_key=api_key)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if not self.api_key:
            raise LLMAdapterError(
                "GROQ_API_KEY is not set. Add it to backend/.env, then restart the server."
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(model=self.model, messages=messages)
        except groq.AuthenticationError as exc:
            raise LLMAdapterError(
                "Groq rejected the configured GROQ_API_KEY. Check that it's set "
                "correctly in backend/.env."
            ) from exc
        except groq.RateLimitError as exc:
            raise LLMAdapterError("Groq's rate limit was hit. Wait a moment and try again.") from exc
        except groq.NotFoundError as exc:
            raise LLMAdapterError(
                f"Model '{self.model}' is not available on Groq. Check LLM_MODEL in backend/.env."
            ) from exc
        except groq.APIConnectionError as exc:
            raise LLMAdapterError(
                "Could not reach Groq's API. Check your internet connection and try again."
            ) from exc
        except groq.APIStatusError as exc:
            raise LLMAdapterError(f"Groq request failed (status {exc.status_code}).") from exc
        except Exception as exc:
            raise LLMAdapterError(f"Unexpected error talking to Groq: {exc}") from exc

        content = response.choices[0].message.content
        return (content or "").strip()

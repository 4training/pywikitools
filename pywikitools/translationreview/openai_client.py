import logging
import time
from typing import Optional

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

MAX_RETRIES: int = 3
RETRY_BACKOFF_SECONDS: float = 2.0
DEFAULT_TIMEOUT_SECONDS: float = 60.0
TIMEOUT_SENTINEL: str = "TIMEOUT"


class OpenAIClient:
    """Thin wrapper around the OpenAI chat completions API with retries."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        request_delay: float = 0.5,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)
        self._model = model
        self._request_delay = request_delay
        self._timeout = timeout
        self.logger = logging.getLogger("pywikitools.translationreview.openai")

    def complete(self, prompt: str) -> str:
        """Send a prompt and return the assistant's text response."""
        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self._timeout,
                )
                content = response.choices[0].message.content
                if content is None:
                    raise RuntimeError("OpenAI returned empty response")
                if self._request_delay > 0:
                    time.sleep(self._request_delay)
                return content.strip()
            except APITimeoutError as err:
                last_error = err
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF_SECONDS * (attempt + 1)
                    self.logger.warning(
                        "OpenAI request timed out (%.0fs), retrying in %.1fs...",
                        self._timeout,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    self.logger.warning(
                        "OpenAI request timed out after %d attempts (%.0fs each)",
                        MAX_RETRIES,
                        self._timeout,
                    )
                    return TIMEOUT_SENTINEL
            except (RateLimitError, APIConnectionError, APIStatusError) as err:
                last_error = err
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF_SECONDS * (attempt + 1)
                    self.logger.warning(
                        "OpenAI request failed (%s), retrying in %.1fs...",
                        err,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError(
            f"OpenAI request failed after {MAX_RETRIES} attempts"
        ) from last_error

"""Ollama API client for LLM interactions."""

import logging
from dataclasses import dataclass

import httpx
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.exceptions import StoryGenerationError

logger = logging.getLogger(__name__)


@dataclass
class OllamaResponse:
    """Response from Ollama API."""

    text: str
    model: str
    done: bool


class OllamaClient:
    """Client for interacting with Ollama API with retry support."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        """
        Initialize Ollama client.

        Args:
            host: Ollama server URL (defaults to settings.OLLAMA_HOST)
            model: Model name (defaults to settings.OLLAMA_MODEL)
            timeout: Request timeout in seconds (defaults to settings.CHAPTER_GENERATION_TIMEOUT)
        """
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        read_timeout = timeout or settings.CHAPTER_GENERATION_TIMEOUT
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=float(read_timeout),
            write=10.0,
            pool=5.0,
        )

    @retry(  # type: ignore[untyped-decorator]
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    def generate_sync(
        self, prompt: str, system: str | None = None
    ) -> OllamaResponse:
        """
        Synchronous generation with automatic retry on transient errors.

        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt

        Returns:
            OllamaResponse with generated text

        Raises:
            StoryGenerationError: If generation fails after retries
        """
        logger.info(f"Generating with model {self.model} at {self.host}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload: dict[str, str | bool] = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
                if system:
                    payload["system"] = system

                response = client.post(
                    f"{self.host}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    text=data.get("response", ""),
                    model=data.get("model", self.model),
                    done=data.get("done", True),
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code}")
            raise StoryGenerationError(
                f"Ollama API error: {e.response.status_code}"
            ) from e
        except httpx.TimeoutException as e:
            logger.error("Ollama request timed out")
            raise StoryGenerationError("Ollama request timed out") from e
        except httpx.NetworkError as e:
            logger.error(f"Network error connecting to Ollama: {e}")
            raise StoryGenerationError(f"Network error: {e}") from e

    async def generate(self, prompt: str, system: str | None = None) -> OllamaResponse:
        """
        Async generation for use in async views.

        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt

        Returns:
            OllamaResponse with generated text

        Raises:
            StoryGenerationError: If generation fails
        """
        logger.info(f"Generating (async) with model {self.model} at {self.host}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload: dict[str, str | bool] = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
                if system:
                    payload["system"] = system

                response = await client.post(
                    f"{self.host}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    text=data.get("response", ""),
                    model=data.get("model", self.model),
                    done=data.get("done", True),
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code}")
            raise StoryGenerationError(
                f"Ollama API error: {e.response.status_code}"
            ) from e
        except httpx.TimeoutException as e:
            logger.error("Ollama request timed out")
            raise StoryGenerationError("Ollama request timed out") from e
        except httpx.NetworkError as e:
            logger.error(f"Network error connecting to Ollama: {e}")
            raise StoryGenerationError(f"Network error: {e}") from e

    def is_available(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
                response = client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False


# Singleton instance for convenience
ollama_client = OllamaClient()

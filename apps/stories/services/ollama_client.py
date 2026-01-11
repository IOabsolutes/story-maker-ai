"""Ollama API client for LLM interactions."""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

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
        self.timeout = timeout or settings.CHAPTER_GENERATION_TIMEOUT

    async def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama API.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text response

        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Placeholder implementation - will be completed in Stage 2
        logger.info(f"Generating with model {self.model} at {self.host}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def generate_sync(self, prompt: str) -> str:
        """
        Synchronous version of generate for use in Celery tasks.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text response
        """
        # Placeholder implementation - will be completed in Stage 2
        logger.info(f"Generating (sync) with model {self.model} at {self.host}")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def check_health(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

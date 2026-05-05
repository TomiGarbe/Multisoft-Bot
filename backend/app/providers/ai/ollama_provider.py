import logging
from typing import Any

import httpx
from app.interfaces.ai.ai_interface import AIInterface
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIInterface):
    """Ollama AI Provider implementation"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.token = settings.OLLAMA_TOKEN

    async def generate(self, prompt: str) -> str:
        data = await self.generate_with_metadata(prompt)
        return str(data.get("response", ""))

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        """
        Generate a response using Ollama AI.
        
        Args:
            prompt: The input prompt for the AI model
            
        Returns:
            The generated text response from Ollama
            
        Raises:
            ValueError: If the response is empty
            httpx.HTTPError: If there's an HTTP error communicating with Ollama
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=300.0  # 5 minutes timeout for AI generation
                )
                response.raise_for_status()
                
                data = response.json()

                # Extract the generated text from response
                generated_text = data.get("response", "").strip()
                
                if not generated_text:
                    raise ValueError("Empty response received from Ollama")
                
                logger.info("[OLLAMA] Generated response for prompt: %.50s...", prompt)
                return {
                    "response": generated_text,
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                    "model": data.get("model") or self.model,
                }

        except httpx.HTTPError as e:
            logger.error("[OLLAMA] HTTP error: %s", e)
            raise
        except ValueError as e:
            logger.error("[OLLAMA] Invalid response: %s", e)
            raise
        except Exception as e:
            logger.error("[OLLAMA] Unexpected error: %s", e)
            raise

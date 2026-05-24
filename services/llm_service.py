"""
LLM Service — OpenAI-compatible API client.

Sends lawyer queries to the LLM and returns responses.
Uses the Drytis OpenAI-compatible gateway.
"""

import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """Client for OpenAI-compatible LLM API."""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, query: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 2000) -> Dict:
        """
        Generate a response from the LLM.

        Args:
            query: The lawyer's question
            system_prompt: Optional system prompt to guide the response
            max_tokens: Maximum tokens in response

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": query})

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return {
                "content": content,
                "model": data.get("model", self.model),
                "usage": usage,
                "success": True,
            }

        except requests.RequestException as e:
            logger.error(f"LLM API error: {e}")
            return {
                "content": f"Error generating response: {str(e)}",
                "model": self.model,
                "usage": {},
                "success": False,
                "error": str(e),
            }

    def generate_legal_memo(self, query: str, matter_context: str = "") -> Dict:
        """
        Generate a legal memo response with citations.

        Args:
            query: Lawyer's question
            matter_context: Context about the legal matter

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        system_prompt = (
            "You are an expert Indian legal research assistant. "
            "Provide detailed legal analysis with case citations. "
            "Use standard Indian legal citation formats: "
            "SCC format like (2024) 5 SCC 123, "
            "AIR format like AIR 2024 SC 123, "
            "SCC OnLine format like 2024 SCC OnLine Del 456, "
            "Cri LJ format like 2024 Cri LJ 789, "
            "SCR format like (2024) 5 SCR 123, and "
            "MANU format like MANU/SC/0123/2024. "
            "Cite real cases whenever possible. Be thorough and precise."
        )

        full_query = query
        if matter_context:
            full_query = f"Context: {matter_context}\n\nQuestion: {query}"

        return self.generate(full_query, system_prompt=system_prompt, max_tokens=3000)

    def generate_generic(self, query: str) -> Dict:
        """
        Generate a generic AI response (no system prompt, no legal guidance).
        This simulates what a plain LLM would produce without BRAHMO's safety layer.

        Args:
            query: Lawyer's question

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        return self.generate(query, max_tokens=3000)
"""
IMS AstroBot — LLM Provider Manager
Manages provider selection, fallback chain, and generation routing.
"""

import threading
from typing import Optional

from rag.providers.base import LLMProvider
from rag.providers.ollama_provider import OllamaProvider
from rag.providers.groq_provider import GroqProvider
from rag.providers.gemini_provider import GeminiProvider

# Thread-safe singleton
_manager_instance: Optional["ProviderManager"] = None
_manager_lock = threading.Lock()


def get_manager() -> "ProviderManager":
    """Get or create the singleton ProviderManager."""
    global _manager_instance
    if _manager_instance is not None:
        return _manager_instance
    with _manager_lock:
        if _manager_instance is not None:
            return _manager_instance
        _manager_instance = ProviderManager()
        return _manager_instance


def reset_manager():
    """Reset the singleton so it re-reads config on next access."""
    global _manager_instance
    with _manager_lock:
        _manager_instance = None


class ProviderManager:
    """
    Routes LLM requests based on configured mode and fallback chain.

    Modes:
        local_only  — Ollama only
        cloud_only  — Primary cloud → fallback cloud
        hybrid      — Primary → fallback (can mix local and cloud)
    """

    def __init__(self):
        from tests.config import (
            LLM_MODE, LLM_PRIMARY_PROVIDER, LLM_FALLBACK_PROVIDER,
            OLLAMA_BASE_URL, OLLAMA_MODEL,
            GROQ_API_KEY, GROQ_MODEL,
            GEMINI_API_KEY, GEMINI_MODEL,
        )

        self.mode = LLM_MODE
        self.primary_name = LLM_PRIMARY_PROVIDER
        self.fallback_name = LLM_FALLBACK_PROVIDER

        # Instantiate all providers (they lazy-connect on first use)
        self._providers: dict[str, LLMProvider] = {
            "ollama": OllamaProvider(OLLAMA_BASE_URL, OLLAMA_MODEL),
            "groq": GroqProvider(GROQ_API_KEY, GROQ_MODEL),
            "gemini": GeminiProvider(GEMINI_API_KEY, GEMINI_MODEL),
        }

    def _get_chain(self) -> list[LLMProvider]:
        """Build the ordered list of providers to try based on mode."""
        if self.mode == "local_only":
            return [self._providers["ollama"]]
        elif self.mode == "cloud_only":
            chain = []
            if self.primary_name in self._providers and self.primary_name != "ollama":
                chain.append(self._providers[self.primary_name])
            if (self.fallback_name and self.fallback_name != "none"
                    and self.fallback_name in self._providers
                    and self.fallback_name != self.primary_name):
                chain.append(self._providers[self.fallback_name])
            return chain
        else:  # hybrid
            chain = []
            if self.primary_name in self._providers:
                chain.append(self._providers[self.primary_name])
            if (self.fallback_name and self.fallback_name != "none"
                    and self.fallback_name in self._providers
                    and self.fallback_name != self.primary_name):
                chain.append(self._providers[self.fallback_name])
            # In hybrid mode, always have ollama as last resort if not already in chain
            ollama = self._providers["ollama"]
            if ollama not in chain:
                chain.append(ollama)
            return chain

    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> Optional[str]:
        """
        Try each provider in the chain until one succeeds.
        Returns the response text, or None if all providers fail.
        """
        chain = self._get_chain()
        last_error = None
        for provider in chain:
            try:
                result = provider.generate(system_prompt, user_message, temperature, max_tokens)
                if result:
                    return result
            except Exception as e:
                last_error = e
                print(f"[ProviderManager] {provider.name} failed: {e}")
                continue
        if last_error:
            print(f"[ProviderManager] All providers failed. Last error: {last_error}")
        return None

    def is_any_available(self) -> bool:
        """Return True if at least one provider in the chain is available."""
        chain = self._get_chain()
        return any(p.is_available() for p in chain)

    def get_all_statuses(self) -> dict[str, dict]:
        """Return status dict for every provider, plus active mode info."""
        statuses = {}
        for key, provider in self._providers.items():
            statuses[key] = provider.get_status()
        statuses["_mode"] = {
            "mode": self.mode,
            "primary": self.primary_name,
            "fallback": self.fallback_name,
        }
        return statuses

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a specific provider by key name."""
        return self._providers.get(name)

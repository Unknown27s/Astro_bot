"""
IMS AstroBot — LLM Provider Base Class
Abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System instruction text.
            user_message: The user's message (includes context + question).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.

        Returns:
            Generated text string.

        Raises:
            Exception on provider errors (caller handles fallback).
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""

    @abstractmethod
    def get_status(self) -> dict:
        """
        Return provider health status dict.
        Keys: 'status' ('ok' | 'warning' | 'error'), 'message' (str).
        """

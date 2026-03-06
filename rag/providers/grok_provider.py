"""
IMS AstroBot — xAI Grok LLM Provider
Connects to the xAI Grok API (OpenAI-compatible chat completions).
"""

import requests
from rag.providers.base import LLMProvider

_GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class GrokProvider(LLMProvider):
    """LLM provider using xAI Grok API."""

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "Grok (xAI)"

    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(_GROK_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def is_available(self) -> bool:
        return bool(self._api_key) and self._test_connection()

    def get_status(self) -> dict:
        if not self._api_key:
            return {"status": "error", "message": "API key not configured"}
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }
            resp = requests.post(_GROK_API_URL, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                return {"status": "ok", "message": f"Model '{self._model}' ready"}
            elif resp.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            else:
                return {"status": "error", "message": f"API error: {resp.status_code}"}
        except requests.ConnectionError:
            return {"status": "error", "message": "Cannot connect to xAI API"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _test_connection(self) -> bool:
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }
            resp = requests.post(_GROK_API_URL, json=payload, headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

"""
IMS AstroBot — Google Gemini LLM Provider
Connects to the Gemini REST API (generativelanguage.googleapis.com).
"""

import requests
from rag.providers.base import LLMProvider

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """LLM provider using Google Gemini API."""

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "Gemini (Google)"

    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> str:
        url = f"{_GEMINI_BASE}/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_message}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
        return ""

    def is_available(self) -> bool:
        return bool(self._api_key) and self._test_connection()

    def get_status(self) -> dict:
        if not self._api_key:
            return {"status": "error", "message": "API key not configured"}
        try:
            url = f"{_GEMINI_BASE}/{self._model}:generateContent?key={self._api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "hi"}]}],
                "generationConfig": {"maxOutputTokens": 1},
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return {"status": "ok", "message": f"Model '{self._model}' ready"}
            elif resp.status_code == 400:
                body = resp.json()
                msg = body.get("error", {}).get("message", "Bad request")
                return {"status": "error", "message": msg}
            elif resp.status_code == 403:
                return {"status": "error", "message": "Invalid API key or quota exceeded"}
            else:
                return {"status": "error", "message": f"API error: {resp.status_code}"}
        except requests.ConnectionError:
            return {"status": "error", "message": "Cannot connect to Gemini API"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _test_connection(self) -> bool:
        try:
            url = f"{_GEMINI_BASE}/{self._model}:generateContent?key={self._api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "hi"}]}],
                "generationConfig": {"maxOutputTokens": 1},
            }
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

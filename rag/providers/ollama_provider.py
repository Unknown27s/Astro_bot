"""
IMS AstroBot — Ollama LLM Provider
Connects to a local Ollama server via its REST API.
"""

import requests
from rag.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using a local Ollama instance."""

    def __init__(self, base_url: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "Ollama (Local)"

    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> str:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self._model == m or self._model == m.split(":")[0] for m in models)
        except Exception:
            return False

    def get_status(self) -> dict:
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return {"status": "error", "message": f"Ollama server returned {resp.status_code}"}
            models = [m["name"] for m in resp.json().get("models", [])]
            if not models:
                return {"status": "warning", "message": "Ollama running but no models pulled"}
            found = any(self._model == m or self._model == m.split(":")[0] for m in models)
            if found:
                return {"status": "ok", "message": f"Model '{self._model}' ready"}
            return {"status": "warning",
                    "message": f"Model '{self._model}' not found. Available: {', '.join(models[:5])}"}
        except Exception as e:
            err = str(e)
            if "Connection" in type(e).__name__ or "refused" in err.lower():
                return {"status": "error", "message": "Cannot connect to Ollama server"}
            return {"status": "error", "message": err[:120]}

    def list_models(self) -> list[str]:
        """Return list of models available on the Ollama server."""
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

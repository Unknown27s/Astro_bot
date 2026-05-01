"""
IMS AstroBot — Groq LLM Provider
Connects to the Groq API (OpenAI-compatible chat completions).
"""

import requests
from rag.providers.base import LLMProvider

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """LLM provider using Groq API."""

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "Groq"

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
        resp = requests.post(_GROQ_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def generate_stream(self, system_prompt: str, user_message: str,
                        temperature: float, max_tokens: int):
        import json
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
            "stream": True,
        }
        with requests.post(_GROQ_API_URL, json=payload, headers=headers, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith("data: "):
                        data_text = line_text[6:]
                        if data_text.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_text)
                            chunk = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            continue

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
            resp = requests.post(_GROQ_API_URL, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                return {"status": "ok", "message": f"Model '{self._model}' ready"}
            elif resp.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            else:
                return {"status": "error", "message": f"API error: {resp.status_code}"}
        except requests.ConnectionError:
            return {"status": "error", "message": "Cannot connect to Groq API"}
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
            resp = requests.post(_GROQ_API_URL, json=payload, headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

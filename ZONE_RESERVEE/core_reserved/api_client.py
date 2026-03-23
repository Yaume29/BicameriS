import json
import requests
import os
from typing import List, Dict, Optional


class APIClient:
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get_models(self) -> List[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/api/v1/models", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            return [{"error": str(e)}]

    def get_loaded_model(self) -> Optional[str]:
        models = self.get_models()
        for model in models:
            loaded_instances = model.get("loaded_instances", [])
            if loaded_instances and len(loaded_instances) > 0:
                return model.get("id")
        return None

    def chat(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Dict:
        if model is None:
            model = self.get_loaded_model()
            if model is None:
                model = "local-model"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Try OpenAI-compatible endpoint first
        endpoints = [
            f"{self.base_url}/v1/chat/completions",
            f"{self.base_url}/api/v1/chat/completions",
            f"{self.base_url}/v1/chat/completions",
        ]

        for endpoint in endpoints:
            try:
                response = self.session.post(endpoint, json=payload, timeout=120)
                if response.status_code == 200:
                    return response.json()
            except requests.exceptions.RequestException:
                continue

        # If all fail, return error
        return {"error": "LM Studio not responding correctly", "choices": []}

    def get_model_info(self) -> Dict:
        models = self.get_models()
        for model in models:
            if model.get("loaded_instances"):
                return {
                    "id": model.get("id"),
                    "display_name": model.get("display_name"),
                    "architecture": model.get("architecture"),
                    "quantization": model.get("quantization", {}).get("name"),
                    "max_context": model.get("max_context_length"),
                    "params": model.get("params_string"),
                }
        return {"status": "no_model_loaded"}

    def is_ready(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False


_client = None


def get_api_client() -> APIClient:
    global _client
    if _client is None:
        url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234")
        _client = APIClient(url)
    return _client

import os
import requests


class OllamaClient:
    def __init__(self, host=None, model=None):
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt, model=None):
        chosen_model = model or self.model

        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": chosen_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
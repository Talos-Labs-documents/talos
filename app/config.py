from dataclasses import dataclass


@dataclass
class Settings:
    ollama_host: str = "http://localhost:11434"
    default_model: str = "llama3"
    max_retries: int = 1
    debug: bool = True
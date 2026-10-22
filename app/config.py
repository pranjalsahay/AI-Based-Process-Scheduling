"""Application configuration and environment management."""

import os
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    PROJECT_NAME: str = "SchedulAI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "schedulai:latest"
    OLLAMA_FALLBACK_MODELS: list = ["qwen2.5:14b-instruct-q3_K_M", "qwen2.5:14b", "llama3.1:latest", "qwen2.5:7b"]
    LLM_TEMPERATURE: float = 0.2
    INFERENCE_TIMEOUT_SECONDS: float = 60.0

    # RAG Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHUNK_SIZE_CHARS: int = 1500
    CHUNK_OVERLAP_CHARS: int = 250
    TOP_K_RETRIEVAL: int = 2

    # Database Settings
    DATABASE_URL: str = "sqlite:///./data/schedulai.db"

    # Scheduling Defaults
    DEFAULT_ROUND_ROBIN_QUANTUM: float = 2.0
    DEFAULT_PRIORITY_CONVENTION: str = "lower_is_higher"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def inspect_hardware_resources() -> Dict[str, Any]:
    """Inspects available RAM, CPU cores, and disk space for local inference sizing."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(".")
    return {
        "total_ram_gb": round(vm.total / (1024 ** 3), 2),
        "available_ram_gb": round(vm.available / (1024 ** 3), 2),
        "cpu_count": psutil.cpu_count(logical=True),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
    }

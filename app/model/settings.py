"""Environment-driven application settings."""
import os
from dotenv import load_dotenv

load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama/qwen2.5:7b")
CREW_VERBOSE = os.getenv("CREW_VERBOSE", "false").lower() in {"1", "true", "yes", "on"}

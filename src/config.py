# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.0.164:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/db/database.db")
# PostgreSQL example: postgresql://user:password@postgres:5432/dbname

# FastAPI configuration
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
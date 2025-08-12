# ai_agent/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[1]  # repo root (one level up from ai_agent/)
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH)

# OpenAI / ChatGPT
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # cambia si usas otro modelo

# Claude (opcional) - configure endpoint and key if you have access
CLAUDE_ENDPOINT = os.getenv("CLAUDE_ENDPOINT", "")  # e.g. "https://api.claude.ai/v1/..."
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# Git + repo
GIT_REMOTE = os.getenv("REMOTE_NAME", "origin")
GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME", "AI Agent")
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "ai@example.com")

# Behaviour toggles
AUTO_PUSH_DEFAULT = os.getenv("AUTO_PUSH", "false").lower() in ("1", "true", "yes")
DRY_RUN_DEFAULT = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")

# Paths for sync & logs
AI_SYNC_DIR = ROOT / "ai_sync"
AI_SYNC_DIR.mkdir(exist_ok=True)
AI_LOG_DIR = ROOT / "ai_logs"
AI_LOG_DIR.mkdir(exist_ok=True)

DEV_NOTES = AI_SYNC_DIR / "dev_notes.json"
REVIEW_REPORT = AI_SYNC_DIR / "review_report.json"
AI_RESPONSE_FILE = ROOT / "ai_response.md"
AI_SUGGESTED_DIR = ROOT / "ai_suggested"
AI_SUGGESTED_DIR.mkdir(exist_ok=True)

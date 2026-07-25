from pathlib import Path

from dotenv import load_dotenv

import os

ROOT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "Project Audo")
APP_ENV = os.getenv("APP_ENV", "development")

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

LOGS_DIR = PROJECT_ROOT / "logs"

TEMPLATES_DIR = PROJECT_ROOT / "app" / "web" / "templates"

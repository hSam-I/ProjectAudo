from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

APP_NAME = "Project Audo"
VERSION = "0.1.0"

DATA_DIR = ROOT_DIR / "datasets"
MODELS_DIR = ROOT_DIR / "models"
LOGS_DIR = ROOT_DIR / "logs"
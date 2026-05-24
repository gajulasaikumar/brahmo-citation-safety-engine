import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "brahmo-dev-secret-key-change-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database — build URI from individual env vars (Drytis provides these)
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "brahmo_citation_safety")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # LLM API (Hugging Face OpenAI-compatible router)
    LLM_API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("HF_TOKEN", ""))
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://router.huggingface.co/v1")
    LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct:novita")

    # Indian Kanoon API
    IK_API_KEY = os.environ.get("IK_API_KEY", "")
    IK_BASE_URL = os.environ.get("IK_BASE_URL", "https://api.indiankanoon.org")

    # Flask env
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # Cache TTL in days
    CACHE_TTL_DAYS = int(os.environ.get("CACHE_TTL_DAYS", "7"))

    # Current year for hallucination detection
    CURRENT_YEAR = int(os.environ.get("CURRENT_YEAR", "2026"))
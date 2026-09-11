import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "").strip()

    CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))
    RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "40"))
    WRONG_ANSWER_COUNT = 5

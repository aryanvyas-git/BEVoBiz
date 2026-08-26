import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://bevobiz:bevobiz_dev_pw@localhost:5432/bevobiz",
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "insecure-dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Connects as a dedicated low-privilege role (SELECT-only on
    # products/sales/businesses, no access to users) — see
    # db/init/002_nlq_readonly_role.sql and app/nlq/db.py. The NLQ safe
    # executor uses this instead of DATABASE_URL; nothing else does.
    NLQ_DATABASE_URL: str = os.getenv(
        "NLQ_DATABASE_URL",
        "postgresql+psycopg://bevobiz_nlq_reader:bevobiz_nlq_reader_dev_pw@localhost:5432/bevobiz",
    )


settings = Settings()

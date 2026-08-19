from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReaderPath"
    API_V1_STR: str = "/api"
    DEBUG: bool = True

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.0

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""

    # Auth (Google OAuth + JWT cookie)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    AUTH_SECRET: str = "change-me-in-production"
    FRONTEND_URL: str = "http://localhost:5173"
    # Internal backend origin (uvicorn)
    BACKEND_URL: str = "http://localhost:8000"
    # Browser-facing API base for OAuth redirects. For local Vite proxy use
    # http://localhost:5173/api so Set-Cookie is first-party to the SPA.
    # Falls back to BACKEND_URL when empty.
    PUBLIC_API_URL: str = "http://localhost:5173/api"
    SESSION_COOKIE_NAME: str = "readerpath_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 7  # 7 days

    # External APIs
    SERPER_API_KEY: Optional[str] = None
    GOOGLE_BOOKS_API_KEY: Optional[str] = None

    RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def oauth_redirect_base(self) -> str:
        return (self.PUBLIC_API_URL or self.BACKEND_URL).rstrip("/")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

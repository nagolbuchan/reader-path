from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "BookFinder"
    API_V1_STR: str = "/api"
    DEBUG: bool = True

    # OpenAI / LLM Settings
    # Make switching between models easy by just changing the environment variable
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"        # You can change to gpt-4o if needed
    # TEMPERATURE: float = 0.7 # Optional: Adjust the creativity of the model's responses (0.0 to 1.0)

    # Neo4j Settings
    NEO4J_URI: str
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str

    # Optional
    RATE_LIMIT_PER_MINUTE: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
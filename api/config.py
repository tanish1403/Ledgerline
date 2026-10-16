"""Application settings, read from environment variables (see .env.example)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "reliability-agent-platform"
    environment: str = "dev"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/reliability"
    # Separate DB used by pytest so tests never touch production data.
    test_database_url: str = "postgresql://postgres:postgres@localhost:5432/reliability_test"
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI-compatible LLM endpoint: OmniRoute (default) or Ollama.
    llm_base_url: str = "http://localhost:20128/v1"
    llm_api_key: str = "not-set"
    llm_model: str = "auto"

    # Dev-only default. Real deployments must override it through the environment.
    jwt_secret: str = "change-me-in-dev"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


settings = Settings()

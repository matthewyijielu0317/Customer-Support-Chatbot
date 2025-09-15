from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    environment: str = Field(default="dev", env="ENVIRONMENT")

    # API keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    pinecone_api_key: str = Field(default="", env="PINECONE_API_KEY")

    # Vector / DB / Cache
    pinecone_index: str = Field(default="ecomm-policies-v1")
    postgres_dsn: str = Field(default="", env="POSTGRES_DSN")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    mongodb_uri: str = Field(default="", env="MONGODB_URI")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()



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
    recent_messages_window: int = Field(default=12, env="RECENT_MESSAGES_WINDOW")
    session_redis_ttl_days: int = Field(default=7, env="SESSION_REDIS_TTL_DAYS")
    semantic_cache_namespace: str = Field(default="semantic_cache", env="SEMANTIC_CACHE_NAMESPACE")
    semantic_cache_similarity_threshold: float = Field(default=0.9, env="SEMANTIC_CACHE_SIMILARITY_THRESHOLD")
    session_summary_min_messages: int = Field(default=12, env="SESSION_SUMMARY_MIN_MESSAGES")
    session_summary_history_limit: int = Field(default=40, env="SESSION_SUMMARY_HISTORY_LIMIT")
    session_summary_max_chars: int = Field(default=256, env="SESSION_SUMMARY_MAX_CHARS")
    slack_webhook_url: str = Field(default="", env="SLACK_WEBHOOK_URL")
    slack_bot_token: str = Field(default="", env="SLACK_BOT_TOKEN")
    slack_channel_id: str = Field(default="", env="SLACK_CHANNEL_ID")
    frontend_base_url: str = Field(default="", env="FRONTEND_BASE_URL")
    admin_email: str = Field(default="", env="ADMIN_EMAIL")
    admin_passcode: str = Field(default="", env="ADMIN_PASSCODE")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

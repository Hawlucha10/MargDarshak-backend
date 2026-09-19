"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All app configuration — loaded from .env file automatically."""

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "margdarshak"
    postgres_user: str = "margdarshak"
    postgres_password: str = "changeme_in_production"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "margdarshak"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # JWT
    jwt_secret_key: str = "changeme_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # External APIs
    rscfoss_api_url: str = "https://api.rscfoss.com"

    @property
    def postgres_url(self) -> str:
        """Build the full PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Build the full Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once, reused everywhere."""
    return Settings()

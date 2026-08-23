"""AeroCool-AI Application and System Configuration.

Centralized configuration management powered by Pydantic Settings.
Loads configuration from environment variables and `.env` files with validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and credentials."""

    # --------------------------------------------------------------------------
    # Application & Server Settings
    # --------------------------------------------------------------------------
    env: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        alias="AEROCOOL_ENV",
        description="Current deployment environment",
    )
    debug: bool = Field(
        default=False,
        alias="AEROCOOL_DEBUG",
        description="Enable debug mode and verbose logging",
    )
    app_host: str = Field(
        default="0.0.0.0",
        alias="AEROCOOL_APP_HOST",
        description="Host interface to bind the FastAPI server",
    )
    app_port: int = Field(
        default=8000,
        alias="AEROCOOL_APP_PORT",
        description="Port to bind the FastAPI server",
    )
    api_prefix: str = Field(
        default="/api/v1",
        alias="AEROCOOL_API_PREFIX",
        description="Prefix for API version routing",
    )
    secret_key: str = Field(
        default="aerocool-ai-default-insecure-secret-key-32chars!",
        alias="AEROCOOL_SECRET_KEY",
        description="Cryptographic secret key for signing tokens/sessions",
    )

    # --------------------------------------------------------------------------
    # PostgreSQL / PostGIS Spatial Database Settings
    # --------------------------------------------------------------------------
    postgres_user: str = Field(default="aerocool", alias="POSTGRES_USER")
    postgres_password: str = Field(default="aerocool_secure_pass", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="aerocool_db", alias="POSTGRES_DB")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    @property
    def async_database_url(self) -> str:
        """Return the async SQLAlchemy database connection string."""
        if self.database_url:
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Return the sync SQLAlchemy database connection string."""
        if self.database_url:
            if "+asyncpg" in self.database_url:
                return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --------------------------------------------------------------------------
    # Redis Cache & Message Broker Settings
    # --------------------------------------------------------------------------
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    @property
    def effective_redis_url(self) -> str:
        """Return the effective Redis connection URL."""
        if self.redis_url:
            return self.redis_url
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # --------------------------------------------------------------------------
    # Google Earth Engine (GEE) Credentials
    # --------------------------------------------------------------------------
    gee_service_account: Optional[str] = Field(default=None, alias="GEE_SERVICE_ACCOUNT")
    gee_private_key_file: Optional[str] = Field(default=None, alias="GEE_PRIVATE_KEY_FILE")
    gee_project_id: Optional[str] = Field(default=None, alias="GEE_PROJECT_ID")

    # --------------------------------------------------------------------------
    # Remote Sensing & Meteorological APIs
    # --------------------------------------------------------------------------
    earthdata_username: Optional[str] = Field(default=None, alias="EARTHDATA_USERNAME")
    earthdata_password: Optional[str] = Field(default=None, alias="EARTHDATA_PASSWORD")
    earthdata_bearer_token: Optional[str] = Field(default=None, alias="EARTHDATA_BEARER_TOKEN")

    cds_api_url: str = Field(
        default="https://cds.climate.copernicus.eu/api/v2", alias="CDS_API_URL"
    )
    cds_api_key: Optional[str] = Field(default=None, alias="CDS_API_KEY")

    osm_overpass_url: str = Field(
        default="https://overpass-api.de/api/interpreter", alias="OSM_OVERPASS_URL"
    )

    # --------------------------------------------------------------------------
    # Physics-Informed ML & Storage Paths
    # --------------------------------------------------------------------------
    model_device: str = Field(default="cpu", alias="MODEL_DEVICE")
    model_checkpoint_dir: Path = Field(
        default=Path("./checkpoints"), alias="MODEL_CHECKPOINT_DIR"
    )
    data_cache_dir: Path = Field(default=Path("./data_cache"), alias="DATA_CACHE_DIR")
    batch_size: int = Field(default=64, alias="BATCH_SIZE")

    seb_loss_weight: float = Field(default=0.35, alias="SEB_LOSS_WEIGHT")
    pde_loss_weight: float = Field(default=0.25, alias="PDE_LOSS_WEIGHT")
    data_loss_weight: float = Field(default=0.40, alias="DATA_LOSS_WEIGHT")

    @field_validator("model_checkpoint_dir", "data_cache_dir", mode="after")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure working directories are instantiated on filesystem."""
        try:
            v.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Provide cached instance of global application settings."""
    return Settings()

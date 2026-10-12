"""Application settings and runtime configuration."""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "Orbit Workbench"
    version: str = "1.0.0"
    author: str = "Ryan Vo"
    email: str = "ryandtvo@gmail.com"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = "sqlite:///./data/orbit.db"

    # Authentication & OIDC / Keycloak
    demo_mode: bool = True
    jwt_secret_key: str = "orbit-demo-insecure-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    oidc_issuer_url: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_audience: Optional[str] = None

    # LLM Settings (server-side only)
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_timeout_seconds: float = 15.0

    # CORS origins
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        return v.lower().strip()

    def check_production_safety(self) -> None:
        """Enforces that demo mode is strictly rejected when running in production."""
        is_prod = self.environment in {"production", "prod"}
        if is_prod and self.demo_mode:
            raise RuntimeError(
                "CRITICAL SECURITY VIOLATION: DEMO_MODE=true is strictly forbidden in production. "
                "Disable demo_mode and configure proper Keycloak OIDC issuer credentials."
            )


settings = Settings()

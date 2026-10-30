from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_name: str = "TalentScope API"
    api_version: str = "1.0.0"
    model_version: str = "v1.0"
    artifact_path: str = "artifacts/v1"
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175"
    )
    request_size_limit: int = 1024 * 1024 * 5  # 5 MB
    enable_legacy_v1: bool = False

    # The repository .env also contains database, auth, and LLM settings that
    # are consumed by their owning modules. This settings object only owns the
    # API-specific fields, so unrelated local keys must be ignored here.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

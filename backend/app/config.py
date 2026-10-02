from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_name: str = "TalentScope API"
    api_version: str = "1.0.0"
    model_version: str = "v1.0"
    artifact_path: str = "../artifacts/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    request_size_limit: int = 1024 * 1024 * 5 # 5 MB
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

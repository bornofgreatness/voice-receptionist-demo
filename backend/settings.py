from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    openai_api_key: str = ""
    database_url: str = f"sqlite:///{ROOT / 'data' / 'demo.db'}"
    webhook_secret: str = "dev-secret"
    default_practice_id: str = "spine_demo"


settings = Settings()

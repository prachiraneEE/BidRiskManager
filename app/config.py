from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "bid-risk-manager"
    database_url: str = "sqlite:///./bid_risk_manager.db"
    log_level: str = "INFO"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"


settings = Settings()

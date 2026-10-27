from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./trends.db"
    cors_origins: str = "http://localhost:8678,http://127.0.0.1:8678,https://topics.k4mik4ge.xyz"
    github_token: str = ""
    bluesky_handle: str = ""
    bluesky_app_password: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"


settings = Settings()

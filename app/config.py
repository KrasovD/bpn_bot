from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    SERVSPACE_API_KEY: str
    SERVSPACE_API_BASE: str = "https://api.serverspace.ru"

    LOW_BALANCE_THRESHOLD: float = 300.0
    BALANCE_CHECK_EVERY_SECONDS: int = 300

settings = Settings()
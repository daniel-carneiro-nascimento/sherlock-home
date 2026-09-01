from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_log_level: str = "INFO"

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:14b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

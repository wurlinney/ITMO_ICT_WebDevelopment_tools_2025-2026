from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Time Manager API"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://app_user:app_password@127.0.0.1:5432/time_manager"
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    parser_service_url: str = "http://127.0.0.1:8001"
    celery_broker_url: str = "redis://127.0.0.1:6379/0"
    celery_result_backend: str = "redis://127.0.0.1:6379/1"
    periodic_parse_url: str = "https://example.com/"
    periodic_parse_interval_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MAX_TEXT_LEN: int = 10000
    MAX_CHUNK_LEN: int = 3000
    MAX_QUEUE_SIZE: int = 10
    NUM_WORKERS: int = 1
    JOB_TTL_SEC: int = 3600
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_INTERVAL_SEC: int = 60
    PREVIEW_RATE_LIMIT: int = 3
    PREVIEW_INTERVAL_SEC: int = 60
    SYNTHESIS_TIMEOUT: int = 180
    PREVIEW_TIMEOUT: int = 15
    CLEANUP_INTERVAL: int = 300
    MAX_REQUEST_BODY_BYTES: int = 31457280
    ADMIN_SESSION_TTL: int = 604800
    ADMIN_LOGIN_ATTEMPTS: int = 5
    ADMIN_ATTEMPT_WINDOW_MIN: int = 15
    IP_HASH_SALT: str
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str
    SECRET_KEY: str
    HTTPS_ONLY: bool = False
    TRUST_PROXY: bool = False
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

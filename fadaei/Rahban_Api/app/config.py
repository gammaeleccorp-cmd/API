from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent 


class Settings(BaseSettings):

    SQLALCHEMY_DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'rahban.db'}"

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ADMIN_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env")
    )


settings = Settings()

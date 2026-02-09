from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""
    ALEMBIC_DATABASE_URL: str = ""
    EVALUATION_INTERVAL_SECONDS: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
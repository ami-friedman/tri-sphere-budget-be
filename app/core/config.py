from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"


settings = Settings()

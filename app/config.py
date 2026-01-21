import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/homestuff",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    APP_NAME = os.environ.get("APP_NAME", "HomeStuff")

    @staticmethod
    def from_env():
        env_name = os.environ.get("FLASK_ENV")
        if env_name and env_name.lower() == "production":
            return ProductionConfig()
        return DevelopmentConfig()


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


def load_config():
    return Config.from_env()

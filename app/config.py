import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Railway provides DATABASE_URL starting with postgres://
    # SQLAlchemy needs postgresql:// so we fix it if needed
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/homestuff",
    )
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url
    
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

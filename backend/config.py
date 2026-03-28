"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "audiobook_platform")

    # Data storage
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    AUDIO_DIR: str = os.path.join(DATA_DIR, "audio")
    OUTPUT_DIR: str = os.path.join(DATA_DIR, "output")

    # Auth
    TOKEN_SECRET: str = os.getenv("TOKEN_SECRET", "dev_secret")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy database URL."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    def ensure_data_dirs(self) -> None:
        """Create data directories if they don't exist."""
        os.makedirs(self.AUDIO_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)


settings = Settings()

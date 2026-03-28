"""Database connection pool using SQLAlchemy Core with pymysql."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from config import settings


engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)


@contextmanager
def get_db() -> Generator:
    """Context manager for database connections."""
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_connection() -> bool:
    """Check if database connection is available."""
    try:
        with get_db() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

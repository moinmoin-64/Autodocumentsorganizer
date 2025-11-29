"""
Database Configuration für SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from pathlib import Path

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/database.db')
# Use absolute path to avoid issues
if not os.path.isabs(DATABASE_PATH):
    DATABASE_PATH = os.path.abspath(DATABASE_PATH)

DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)

@contextmanager
def get_db():
    """Context Manager für DB-Sessions"""
    db = Session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialisiert Datenbank-Tabellen"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

"""SQLAlchemy database setup.

Uses the DATABASE_URL environment variable so the same code runs on
SQLite (local development / low-resource machines) and MySQL
(production, as per the project proposal).

    # local dev (default)
    DATABASE_URL=sqlite:///./fyp.db
    # production MySQL
    DATABASE_URL=mysql+pymysql://fyp_user:secret@localhost:3306/fyp_contraband
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from . import app_config

DATABASE_URL = app_config.DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401  (register models before create_all)
    Base.metadata.create_all(bind=engine)

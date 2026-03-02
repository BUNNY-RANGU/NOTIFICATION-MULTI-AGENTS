# web/database.py
# =====================================================
# JOB: Connect to SQLite database
# SQLite = single file database, zero setup needed!
# All data saved in shop_data.db file
# =====================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database file location
# All data saved here automatically
DATABASE_URL = "sqlite:///./shop_data.db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session factory
# Session = one conversation with database
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all our database models
Base = declarative_base()


def get_db():
    """
    Creates a database session.
    Used by FastAPI routes to talk to database.
    Always closes session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Creates all database tables.
    Run this once when app starts.
    """
    from web.models import Shop, DailyReport, InventorySnapshot
    Base.metadata.create_all(bind=engine)
    print("Database initialized!")
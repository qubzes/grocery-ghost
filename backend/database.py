from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
)
from typing import Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

Base = declarative_base()


class Scrape(Base):
    __tablename__ = "scrapes"
    id = Column(String, primary_key=True, index=True)
    url = Column(String, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="pending")
    progress = Column(String, default="")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    scrape_id = Column(String, ForeignKey("scrapes.id"))
    current_price: Column[float] = Column(Float)
    original_price: Column[Optional[float]] = Column(Float, nullable=True)
    unit_size = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    department = Column(String, nullable=True)
    dietary_tags = Column(String, nullable=True)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

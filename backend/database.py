from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
import sqlite3

# Optimized SQLite configuration for performance and to prevent locking
engine = create_engine(
    "sqlite:///grocery_ghost.db",
    echo=False,  # Set to True for debugging SQL queries
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=20,  # Increase pool size for better concurrency
    max_overflow=30,  # Allow more overflow connections
    connect_args={
        "check_same_thread": False,  # Allow sharing connections across threads
        "timeout": 60,  # Increased timeout for database operations
    }
)

# SQLite optimization pragma settings
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        # Performance optimizations
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between speed and safety
        cursor.execute("PRAGMA cache_size=10000")  # Increase cache size
        cursor.execute("PRAGMA temp_store=MEMORY")  # Store temporary tables in memory
        cursor.execute("PRAGMA mmap_size=268435456")  # Use memory mapping (256MB)
        cursor.execute("PRAGMA busy_timeout=60000")  # 60 second busy timeout
        cursor.execute("PRAGMA wal_autocheckpoint=1000")  # Auto-checkpoint every 1000 pages
        cursor.execute("PRAGMA optimize")  # Optimize the database
        cursor.close()

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

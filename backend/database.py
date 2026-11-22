import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def init_engine():
    mysql_url = settings.get_database_url()
    try:
        # Attempt connecting to MySQL with 3s timeout
        engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 3}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to MySQL database: %s", settings.MYSQL_DATABASE)
        return engine, "mysql"
    except Exception as e:
        logger.warning("Could not connect to MySQL at %s:%s - %s", settings.MYSQL_HOST, settings.MYSQL_PORT, e)
        if settings.ALLOW_SQLITE_FALLBACK:
            sqlite_url = "sqlite:///./multimodal_companion_dev.db"
            logger.info("Fallback to local SQLite database: %s", sqlite_url)
            fallback_engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine, "sqlite"
        else:
            raise ConnectionError(f"Failed to connect to MySQL database and fallback is disabled: {e}")

engine, DB_DIALECT = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all declarative tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully on dialect '%s'.", DB_DIALECT)

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings





engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False      # Only for SQLite
    },
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

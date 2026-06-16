import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

Base = declarative_base()

_engine = None
_AsyncSessionLocal = None

def get_engine():
    global _engine, _AsyncSessionLocal
    if _engine is None:
        if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
            missing = [k for k, v in {"DB_USER": DB_USER, "DB_PASSWORD": DB_PASSWORD, "DB_HOST": DB_HOST, "DB_NAME": DB_NAME}.items() if not v]
            raise RuntimeError(f"Missing required database environment variables: {', '.join(missing)}")
        DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        _engine = create_async_engine(DATABASE_URL, echo=False)
        _AsyncSessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine, _AsyncSessionLocal

class AsyncSessionLocal:
    """Proxy class that lazily initializes the session factory."""
    def __new__(cls):
        _, session_factory = get_engine()
        return session_factory()

async def get_db():
    _, session_factory = get_engine()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

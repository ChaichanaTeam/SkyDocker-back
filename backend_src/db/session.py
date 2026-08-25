from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend_src.core import Settings

engine: Engine = create_async_engine(Settings.DATABASE_URL, echo=Settings.DEBUG, pool_pre_ping=True) # type: ignore

AsyncSessionMaker: async_sessionmaker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine) # type: ignore
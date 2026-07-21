from app.core.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///./test_vocentra.db"

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.core.database import Base, engine, AsyncSessionLocal, get_db
from app.main import app

TestingSessionLocal = AsyncSessionLocal


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

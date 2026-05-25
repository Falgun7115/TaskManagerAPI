import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

load_dotenv()

_raw_url = os.getenv("DATABASE_URL", "")

# Normalize DATABASE_URL to asyncpg format
if _raw_url.startswith("postgresql+asyncpg://"):
    DATABASE_URL = _raw_url

elif _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )

elif _raw_url.startswith("postgres://"):
    DATABASE_URL = _raw_url.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1,
    )

else:
    DATABASE_URL = _raw_url

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Disable pooling for tests
test_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def clear_tables():
    """Drop and recreate all tables before each test."""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


async def override_get_db():
    """Override database dependency for tests."""

    async with TestingSessionLocal() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_root():
    """Test root endpoint."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_task():
    """Test creating a task."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "This is a test task",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Test Task"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_all_tasks():
    """Test fetching all tasks."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_single_task():
    """Test fetching one task."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/tasks",
            json={"title": "Single Task"},
        )

        task_id = create_response.json()["id"]

        response = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_not_found():
    """Test fetching missing task."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/tasks/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_status():
    """Test updating task status."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/tasks",
            json={"title": "Status Task"},
        )

        task_id = create_response.json()["id"]

        response = await client.patch(
            f"/tasks/{task_id}/status",
            json={"status": "completed"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_update_task_invalid_status():
    """Test invalid status update."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/tasks",
            json={"title": "Invalid Status Task"},
        )

        task_id = create_response.json()["id"]

        response = await client.patch(
            f"/tasks/{task_id}/status",
            json={"status": "in-progress"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_task():
    """Test deleting task."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/tasks",
            json={"title": "Delete Me"},
        )

        task_id = create_response.json()["id"]

        response = await client.delete(f"/tasks/{task_id}")

        assert response.status_code == 200

        get_response = await client.get(f"/tasks/{task_id}")

        assert get_response.status_code == 404

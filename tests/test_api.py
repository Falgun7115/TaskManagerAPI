import os
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from app.main import (
    create_task,
    delete_task,
    home,
    show_by_id,
    update_task,
)
from app.model import Task
from app.schema import (
    TaskCreate,
    TaskStatusUpdate,
)


os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://test:test@localhost/test"
)


@pytest.mark.asyncio
async def test_home():
    """Test root endpoint."""

    response = await home()

    assert response == {
        "message": "Task manager API is running",
    }


@pytest.mark.asyncio
async def test_create_task():
    """Unit test for creating task."""

    mock_db = AsyncMock()

    task_data = TaskCreate(
        title="Test Task",
        description="Testing",
    )

    response = await create_task(
        task=task_data,
        db=mock_db,
    )

    assert response.title == "Test Task"
    assert response.status == "pending"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_show_task_by_id():
    """Unit test for fetching single task."""

    mock_task = Task(
        id=1,
        title="Sample Task",
        status="pending",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    response = await show_by_id(
        task_id=1,
        db=mock_db,
    )

    assert response.id == 1
    assert response.title == "Sample Task"


@pytest.mark.asyncio
async def test_show_task_not_found():
    """Unit test for missing task."""

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await show_by_id(
            task_id=999,
            db=mock_db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Task not found"


@pytest.mark.asyncio
async def test_update_task_status():
    """Unit test for updating task status."""

    mock_task = Task(
        id=1,
        title="Task",
        status="pending",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    response = await update_task(
        task_id=1,
        request_status=TaskStatusUpdate(
            status="completed",
        ),
        db=mock_db,
    )

    assert response.status == "completed"

    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_task():
    """Unit test for deleting task."""

    mock_task = Task(
        id=1,
        title="Delete Task",
        status="pending",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    response = await delete_task(
        task_id=1,
        db=mock_db,
    )

    assert response == {
        "message": (
            "Record id 1 deleted successfully"
        ),
    }

    mock_db.delete.assert_awaited_once()
    mock_db.commit.assert_awaited_once()

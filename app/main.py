from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.model as model
import app.schema as schema
from app.database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(model.Base.metadata.create_all)
    yield


app = FastAPI(title="Task Management API", lifespan=lifespan)


@app.get("/")
async def home():
    """Root endpoint."""
    return "Task manager API is running"


@app.post(
    "/tasks",
    response_model=schema.TaskResponse,
    status_code=201,
)
async def create_task(
    task: schema.TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    new_task = model.Task(
        title=task.title,
        description=task.description,
        status="pending",
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@app.get(
    "/tasks",
    response_model=List[schema.TaskResponse],
    status_code=200,
)
async def show_all(db: AsyncSession = Depends(get_db)):
    """Fetch all tasks."""
    result = await db.execute(select(model.Task))
    return result.scalars().all()


@app.get(
    "/tasks/{task_id}",
    response_model=schema.TaskResponse,
    status_code=200,
)
async def show_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetch task by ID."""
    result = await db.execute(
        select(model.Task).where(model.Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


@app.patch(
    "/tasks/{task_id}/status",
    response_model=schema.TaskResponse,
    status_code=200,
)
async def update_task(
    task_id: int,
    request_status: schema.TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update task status."""
    result = await db.execute(
        select(model.Task).where(model.Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    if request_status.status not in ["pending", "completed"]:
        raise HTTPException(
            status_code=422,
            detail="Status must be 'pending' or 'completed'",
        )

    task.status = request_status.status
    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    return task


@app.delete("/tasks/{task_id}", status_code=200)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete task by ID."""
    result = await db.execute(
        select(model.Task).where(model.Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    await db.delete(task)
    await db.commit()

    return {"message": f"Record id {task_id} deleted successfully"}

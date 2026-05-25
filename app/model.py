from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class Task(Base):
    """
    Task table schema in PostgreSQL.

    Columns:
    - id          : Auto-incremented primary key
    - title       : Short name for the task
    - description : Longer details about the task
    - status      : Either "pending" or "completed"
    - created_at  : Timestamp when task is created
    - updated_at  : Timestamp when task is updated
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(
        String(200),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

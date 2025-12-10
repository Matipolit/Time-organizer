from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict
from sqlmodel import Field, Relationship, SQLModel


class TaskType(str, Enum):
    DEADLINE = "deadline"
    CHORE = "chore"
    STREAK = "streak"


class TaskStatus(str, Enum):
    TODO = "todo"
    DONE = "done"
    # We don't need 'Archived' yet. If a chore is done, it resets to 'Todo' with new date.


# The T-Shirt Sizes (Abstractions for Time)
class EffortLevel(str, Enum):
    S = "S"  # < 15 mins (Quick wins)
    M = "M"  # ~ 1 hour (Standard)
    L = "L"  # ~ 2-3 hours (Deep Work)
    XL = "XL"  # Too big. Needs breakdown.


# single table for all task types
class Task(SQLModel, table=True):
    model_config = ConfigDict(validate_assignment=True)  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None

    task_type: TaskType = Field(index=True)
    status: TaskStatus = Field(default=TaskStatus.TODO)

    # For type: Deadline
    # Soft Deadline
    scheduled_date: Optional[datetime] = Field(default=None, index=True)

    effort: Optional[EffortLevel] = Field(default=None)

    # for nested tasks
    parent_id: Optional[int] = Field(default=None, foreign_key="task.id")

    deadline: Optional[datetime] = None

    # For type: Chores
    # How many days after *completion* should this reappear?
    recurrence_interval_days: Optional[int] = None

    # For type: Streaks
    current_streak: int = Field(default=0)
    best_streak: int = Field(default=0)

    # Metadata / History
    created_at: datetime = Field(default_factory=datetime.now)
    # For calculating the next chore date or checking if a streak is broken
    last_completed_at: Optional[datetime] = None

    children: List["Task"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "remote_side": "Task.parent_id",
        }
    )

    parent: Optional["Task"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Task.id"}
    )


# Response model that includes children for API responses
class TaskRead(SQLModel):
    id: int
    title: str
    description: Optional[str] = None
    task_type: TaskType
    status: TaskStatus
    scheduled_date: Optional[datetime] = None
    effort: Optional[EffortLevel] = None
    parent_id: Optional[int] = None
    deadline: Optional[datetime] = None
    recurrence_interval_days: Optional[int] = None
    current_streak: int = 0
    best_streak: int = 0
    created_at: datetime
    last_completed_at: Optional[datetime] = None
    children: List["TaskRead"] = []

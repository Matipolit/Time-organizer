from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Task, TaskRead, TaskStatus, TaskType, TaskUpdate
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select


def get_children_loader():
    """Create recursive selectinload for children at all levels"""
    return (
        selectinload(Task.children)  # type: ignore
        .selectinload(Task.children)  # type: ignore
        .selectinload(Task.children)  # type: ignore
    )


app = FastAPI()

sqlite_file_name = "planner.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI(title="Flexible Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.0.32",
    ],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/tasks/", response_model=TaskRead)
def create_task(task: Task):
    """
    Create a new task.
    """
    if (
        task.task_type == TaskType.DEADLINE
        and task.parent_id is None
        and task.deadline is None
    ):
        raise HTTPException(
            status_code=400, detail="Root deadline tasks must have a deadline."
        )

    task.status = TaskStatus.TODO
    task.created_at = datetime.now()

    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id: int = task.id  # type: ignore

        # Reload with children to avoid detached instance error
        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        if not reloaded_task:
            raise HTTPException(status_code=500, detail="Failed to reload created task")
        return TaskRead.model_validate(reloaded_task)


@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    only_today: bool = False,
):
    """
    Fetch tasks (only root tasks with children populated).
    - 'only_today': Filters for tasks scheduled for today or earlier (overdue).
    """
    with Session(engine) as session:
        statement = (
            select(Task)
            .where(Task.parent_id == None)  # type: ignore
            .options(get_children_loader())
        )

        if status:
            statement = statement.where(Task.status == status)

        if task_type:
            statement = statement.where(Task.task_type == task_type)

        if only_today:
            # Show tasks with a scheduled_date of today or in the past
            now = datetime.now()
            today_end = now.replace(hour=23, minute=59, second=59)
            statement = statement.where(Task.scheduled_date <= today_end)  # type: ignore

        # Default Sort: Scheduled Date (Ascending), then Priority/Effort
        statement = statement.order_by(Task.scheduled_date)  # type: ignore

        results = session.exec(statement).all()
        # Convert to TaskRead to include children
        return [TaskRead.model_validate(task) for task in results]


@app.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int):
    """
    Fetch a single task by ID with children populated.
    """
    with Session(engine) as session:
        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        task = session.exec(statement).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskRead.model_validate(task)


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_update: TaskUpdate):
    """
    Update task data.
    """
    with Session(engine) as session:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

        task_data = task_update.model_dump(exclude_unset=True)

        db_task.sqlmodel_update(task_data)

        session.add(db_task)
        session.commit()
        session.refresh(db_task)

        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        return TaskRead.model_validate(reloaded_task)


@app.patch("/tasks/{task_id}/done", response_model=TaskRead)
def mark_task_done(task_id: int):
    """
    Mark task as done, handle the following logic depending on task type
    """

    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        now = datetime.now()

        # LOGIC 1: Deadlines (Thesis/Uni)
        if task.task_type == TaskType.DEADLINE:
            task.status = TaskStatus.DONE
            task.last_completed_at = now

        # LOGIC 2: Chores (Maintenance)
        elif task.task_type == TaskType.CHORE:
            # 1. Update the 'last_completed' for record keeping
            task.last_completed_at = now

            # 2. Calculate the next date based on NOW (not the old due date)
            if task.recurrence_interval_days:
                next_date = now + timedelta(days=task.recurrence_interval_days)
                task.scheduled_date = next_date
                # Keep status as TODO so it rotates to the bottom or disappears from 'Today' view
                task.status = TaskStatus.TODO
            else:
                task.status = TaskStatus.DONE
        elif task.task_type == TaskType.STREAK:
            # Logic: Has it been more than 1 day since last completion?
            if task.last_completed_at:
                delta = now - task.last_completed_at
                if delta.days > 1:
                    # Streak broken!
                    task.current_streak = 1
                elif delta.days <= 1:
                    # Streak kept!
                    task.current_streak += 1
            else:
                # First time ever
                task.current_streak = 1

            # Update Best Streak
            if task.current_streak > task.best_streak:
                task.best_streak = task.current_streak

            task.last_completed_at = now
            # Streaks usually stay 'Todo' so you can do them again tomorrow,
            # or you can mark them done for the day. Let's mark Done for Today.
            # (You will need a frontend check to un-done them tomorrow).
            task.status = TaskStatus.DONE

        session.add(task)
        session.commit()
        task_id: int = task.id  # type: ignore

        # Reload with children to avoid detached instance error
        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        if not reloaded_task:
            raise HTTPException(status_code=500, detail="Failed to reload task")
        return TaskRead.model_validate(reloaded_task)


@app.patch("/tasks/{task_id}/undone", response_model=TaskRead)
def mark_task_undone(task_id: int):
    """
    Mark task as undone.
    """

    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Simply revert status to TODO
        task.status = TaskStatus.TODO

        session.add(task)
        session.commit()
        task_id: int = task.id  # type: ignore

        # Reload with children to avoid detached instance error
        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        if not reloaded_task:
            raise HTTPException(status_code=500, detail="Failed to reload task")
        return TaskRead.model_validate(reloaded_task)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
        return {"ok": True}

from datetime import datetime, timedelta
from typing import List, Optional

import markdown_render


def render_description(content: Optional[str]) -> Optional[str]:
    if content is None:
        return None
    return markdown_render.render_to_html(content)


from auth import (
    create_access_token,
    get_credentials_from_env,
    get_current_user,
    verify_password,
)
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from models import Idea, IdeaUpdate, Task, TaskRead, TaskStatus, TaskType, TaskUpdate
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select


def get_children_loader():
    """Create recursive selectinload for children at all levels"""
    return (
        selectinload(Task.children)  # type: ignore
        .selectinload(Task.children)  # type: ignore
        .selectinload(Task.children)  # type: ignore
    )


sqlite_file_name = "planner.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI(title="Flexible Planner API", root_path="/timely/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.0.32",
        "matipolit.ovh",
    ],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    with Session(engine) as session:
        yield session


# Request/Response models for auth
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Login endpoint - returns JWT token"""
    env_username, env_password = get_credentials_from_env()

    if request.username != env_username or request.password != env_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(data={"sub": request.username})
    return TokenResponse(access_token=access_token, token_type="bearer")


@app.get("/auth/verify")
def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verify that the provided token is valid"""
    return {"status": "authenticated", "user": current_user.get("sub")}


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/ideas/", response_model=Idea)
def create_idea(idea: Idea, current_user: dict = Depends(get_current_user)):
    """
    Create a new idea.
    """
    idea.description_html = render_description(idea.description)
    with Session(engine) as session:
        session.add(idea)
        session.commit()
        session.refresh(idea)
        return idea


@app.get("/ideas/", response_model=List[Idea])
def read_ideas(
    current_user: dict = Depends(get_current_user),
):
    """
    Fetch ideas
    """
    with Session(engine) as session:
        statement = select(Idea).order_by(Idea.created_at.desc())  # type: ignore
        results = session.exec(statement).all()
        return list(results)


@app.patch("/ideas/{idea_id}", response_model=Idea)
def update_idea(
    idea_id: int,
    idea_update: IdeaUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update an idea.
    """
    with Session(engine) as session:
        db_idea = session.get(Idea, idea_id)
        if not db_idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        idea_data = idea_update.model_dump(exclude_unset=True)
        db_idea.sqlmodel_update(idea_data)

        if "description" in idea_data:
            db_idea.description_html = render_description(db_idea.description)

        session.add(db_idea)
        session.commit()
        session.refresh(db_idea)
        return db_idea


@app.delete("/ideas/{idea_id}")
def delete_idea(idea_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete an idea.
    """
    with Session(engine) as session:
        db_idea = session.get(Idea, idea_id)
        if not db_idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        session.delete(db_idea)
        session.commit()
        return {"ok": True}


@app.post("/ideas/{idea_id}/convert", response_model=TaskRead)
def convert_idea_to_task(
    idea_id: int,
    task_type: TaskType = TaskType.DEADLINE,
    current_user: dict = Depends(get_current_user),
):
    """
    Convert an idea into a task and delete the original idea.
    """
    with Session(engine) as session:
        db_idea = session.get(Idea, idea_id)
        if not db_idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        new_task = Task(
            title=db_idea.title,
            description=db_idea.description,
            description_html=db_idea.description_html,
            task_type=task_type,
            status=TaskStatus.TODO,
            created_at=datetime.now(),
        )

        session.add(new_task)
        session.delete(db_idea)
        session.commit()
        session.refresh(new_task)

        # Reload with children to avoid detached instance error
        statement = (
            select(Task).where(Task.id == new_task.id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        if not reloaded_task:
            raise HTTPException(status_code=500, detail="Failed to reload created task")
        return TaskRead.model_validate(reloaded_task)


@app.post("/tasks/", response_model=TaskRead)
def create_task(task: Task, current_user: dict = Depends(get_current_user)):
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
    task.description_html = render_description(task.description)

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
    current_user: dict = Depends(get_current_user),
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
def read_task(task_id: int, current_user: dict = Depends(get_current_user)):
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
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update task data.
    """
    with Session(engine) as session:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

        task_data = task_update.model_dump(exclude_unset=True)

        db_task.sqlmodel_update(task_data)

        if "description" in task_data:
            db_task.description_html = render_description(db_task.description)

        session.add(db_task)
        session.commit()
        session.refresh(db_task)

        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        return TaskRead.model_validate(reloaded_task)


@app.patch("/tasks/{task_id}/done", response_model=TaskRead)
def mark_task_done(task_id: int, current_user: dict = Depends(get_current_user)):
    """
    Mark task as done, handle the following logic depending on task type
    """

    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        now = datetime.now()

        # LOGIC 1: Deadlines (Thesis/Uni) AND Todo
        if task.task_type in [TaskType.DEADLINE, TaskType.TODO]:
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


@app.patch("/tasks/{task_id}/start", response_model=TaskRead)
def start_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """
    Mark task as in progress. Also resets any currently in progress task to TODO.
    """
    with Session(engine) as session:
        # Reset other in-progress tasks
        statement = select(Task).where(Task.status == TaskStatus.IN_PROGRESS)
        in_progress_tasks = session.exec(statement).all()
        for t in in_progress_tasks:
            t.status = TaskStatus.TODO
            session.add(t)

        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.status = TaskStatus.IN_PROGRESS
        session.add(task)
        session.commit()

        # Reload with children to avoid detached instance error
        statement = (
            select(Task).where(Task.id == task_id).options(get_children_loader())
        )
        reloaded_task = session.exec(statement).first()
        if not reloaded_task:
            raise HTTPException(status_code=500, detail="Failed to reload task")
        return TaskRead.model_validate(reloaded_task)


@app.patch("/tasks/{task_id}/undone", response_model=TaskRead)
def mark_task_undone(task_id: int, current_user: dict = Depends(get_current_user)):
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
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
        return {"ok": True}

import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.schemas.task import TaskStatus

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    assignee: Mapped[str] = mapped_column(String(100))
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO)
    
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now()
    )
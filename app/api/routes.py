import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.redis import get_redis
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

# Инициализируем логгер для текущего модуля
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Задачи"])


async def clear_tasks_cache(cache: Redis):
    try:
        keys = await cache.keys("tasks_list:*")
        if keys:
            await cache.delete(*keys)
            logger.info(f"Cache cleared for {len(keys)} keys")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_redis),
):
    new_task = Task(**task_in.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    logger.info(f"Task created with ID: {new_task.id}")
    await clear_tasks_cache(cache)
    return new_task


@router.get("/", response_model=List[TaskRead])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    assignee: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_redis),
):
    status_str = status.value if status else "all"
    assignee_str = assignee if assignee else "any"
    cache_key = f"tasks_list:{status_str}:{assignee_str}"

    try:
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return [TaskRead(**item) for item in json.loads(cached_data)]
    except Exception as e:
        logger.warning(f"Failed to read from Redis: {e}")

    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    if assignee:
        query = query.where(Task.assignee.ilike(f"%{assignee}%"))

    result = await db.execute(query)
    tasks = result.scalars().all()

    # Попытка записи в кэш
    try:
        tasks_for_cache = [
            TaskRead.model_validate(t).model_dump(mode="json") for t in tasks
        ]
        await cache.set(cache_key, json.dumps(tasks_for_cache), ex=60)
        logger.info(f"Cache updated for key: {cache_key}")
    except Exception as e:
        logger.warning(f"Failed to write to Redis: {e}")

    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        logger.warning(f"Task lookup failed: ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_redis),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        logger.warning(f"Update failed: ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task_data.status:
        if task.status == TaskStatus.DONE and task_data.status != TaskStatus.DONE:
            logger.info(
                f"Update rejected: Attempt to revert DONE status on ID {task_id}"
            )
            raise HTTPException(
                status_code=400, detail="Нельзя изменить статус из 'done'"
            )

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    logger.info(f"Task updated: ID {task_id}")
    await clear_tasks_cache(cache)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int, db: AsyncSession = Depends(get_db), cache: Redis = Depends(get_redis)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        logger.warning(f"Delete failed: ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")

    await db.delete(task)
    await db.commit()

    logger.info(f"Task deleted: ID {task_id}")
    await clear_tasks_cache(cache)
    return {"status": "ok"}

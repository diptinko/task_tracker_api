import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_task():
    """Тест создания задачи"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/tasks/",
            json={
                "title": "Тестовая задача",
                "description": "Описание",
                "assignee": "Тестировщик",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая задача"
    assert data["status"] == "todo"


@pytest.mark.asyncio
async def test_change_status():
    """Тест смены статуса задачи"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post(
            "/tasks/", json={"title": "Задача для статуса", "assignee": "Тестировщик"}
        )
        task_id = create_res.json()["id"]

        patch_res = await ac.patch(f"/tasks/{task_id}", json={"status": "in_progress"})

    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_done_status_lock():
    """Тест бизнес-логики: блокировка смены статуса из DONE"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post(
            "/tasks/", json={"title": "Завершенная задача", "assignee": "Тестировщик"}
        )
        task_id = create_res.json()["id"]

        await ac.patch(f"/tasks/{task_id}", json={"status": "done"})

        fail_res = await ac.patch(f"/tasks/{task_id}", json={"status": "todo"})

    assert fail_res.status_code == 400

"""
Asynchronous Background Task Manager.

Processes long-running summarization or batch compression jobs asynchronously
without blocking the FastAPI event loop, providing task status tracking.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class BackgroundTask:
    task_id: str
    created_at: float
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None
    duration_ms: float = 0.0


class AsyncTaskQueue:
    """Manages ephemeral background jobs in memory."""

    def __init__(self):
        self._tasks: dict[str, BackgroundTask] = {}

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = BackgroundTask(
            task_id=task_id,
            created_at=time.time(),
            status=TaskStatus.PENDING,
        )
        return task_id

    def get_task(self, task_id: str) -> BackgroundTask | None:
        return self._tasks.get(task_id)

    async def execute_task(self, task_id: str, coro):
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.PROCESSING
        start = time.perf_counter()
        try:
            res = await coro if asyncio.iscoroutine(coro) else coro()
            task.result = res
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
        finally:
            task.duration_ms = round((time.perf_counter() - start) * 1000, 2)


async_task_queue = AsyncTaskQueue()

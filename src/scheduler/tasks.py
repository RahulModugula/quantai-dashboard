"""Task scheduler for background jobs."""
import logging
import asyncio
from typing import Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleType(str, Enum):
    """Schedule types."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScheduledTask:
    """Scheduled task."""

    def __init__(
        self,
        name: str,
        func: Callable,
        schedule_type: ScheduleType = ScheduleType.ONCE,
        schedule_time: datetime = None,
    ):
        """Initialize scheduled task.

        Args:
            name: Task name
            func: Function to execute
            schedule_type: Schedule type
            schedule_time: When to execute
        """
        self.task_id = str(uuid.uuid4())
        self.name = name
        self.func = func
        self.schedule_type = schedule_type
        self.schedule_time = schedule_time or datetime.now()
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "schedule_type": self.schedule_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "error": str(self.error) if self.error else None,
        }


class TaskScheduler:
    """Schedule and manage background tasks."""

    def __init__(self):
        """Initialize task scheduler."""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks = set()

    def schedule(
        self,
        name: str,
        func: Callable,
        schedule_type: ScheduleType = ScheduleType.ONCE,
        schedule_time: datetime = None,
    ) -> ScheduledTask:
        """Schedule a task.

        Args:
            name: Task name
            func: Function to execute
            schedule_type: Schedule type
            schedule_time: When to execute

        Returns:
            Scheduled task
        """
        task = ScheduledTask(name, func, schedule_type, schedule_time)
        self.tasks[task.task_id] = task

        logger.info(
            f"Task scheduled: {name} ({schedule_type.value}) - ID: {task.task_id}"
        )

        return task

    async def execute_task(self, task_id: str) -> bool:
        """Execute a task.

        Args:
            task_id: Task ID

        Returns:
            Whether execution was successful
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return False

        task = self.tasks[task_id]

        if task_id in self.running_tasks:
            logger.warning(f"Task already running: {task_id}")
            return False

        self.running_tasks.add(task_id)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            if asyncio.iscoroutinefunction(task.func):
                task.result = await task.func()
            else:
                task.result = task.func()

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.retry_count = 0

            logger.info(f"Task completed: {task.name} ({task_id})")
            return True

        except Exception as e:
            task.error = e
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                logger.warning(
                    f"Task failed, will retry: {task.name} ({task_id}): {e}"
                )
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task failed permanently: {task.name} ({task_id}): {e}")

            return False

        finally:
            self.running_tasks.discard(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            Whether cancellation was successful
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED

        logger.info(f"Task cancelled: {task.name} ({task_id})")

        return True

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task."""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
    ) -> List[Dict]:
        """List tasks.

        Args:
            status: Filter by status

        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        return [t.to_dict() for t in sorted(
            tasks,
            key=lambda t: t.created_at,
            reverse=True,
        )]

    def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get pending tasks."""
        return [
            t for t in self.tasks.values()
            if t.status == TaskStatus.PENDING
            and t.schedule_time <= datetime.now()
        ]

    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "pending_tasks": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
            ),
            "completed_tasks": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
            ),
            "failed_tasks": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
            ),
        }


# Global task scheduler
_scheduler = TaskScheduler()


def get_scheduler() -> TaskScheduler:
    """Get global task scheduler."""
    return _scheduler


def schedule_task(
    name: str,
    func: Callable,
    schedule_type: ScheduleType = ScheduleType.ONCE,
    schedule_time: datetime = None,
) -> ScheduledTask:
    """Schedule a task globally."""
    scheduler = get_scheduler()
    return scheduler.schedule(name, func, schedule_type, schedule_time)


def execute_task(task_id: str):
    """Execute a task globally."""
    scheduler = get_scheduler()
    return scheduler.execute_task(task_id)

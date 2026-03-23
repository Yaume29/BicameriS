import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str
    priority: int
    created_at: str
    updated_at: str
    tags: List[str]
    details: Dict


class TaskManager:
    def __init__(self, storage_file: str = "ZONE_RESERVEE/logs/tasks.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: List[Task] = self._load_tasks()

    def _load_tasks(self) -> List[Task]:
        if not self.storage_file.exists():
            return []
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Task(**t) for t in data]
        except:
            return []

    def _save_tasks(self):
        data = [asdict(t) for t in self._tasks]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority=TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
    ) -> Task:
        now = datetime.now().isoformat()
        task = Task(
            id=f"task_{now.replace('.', '_')}",
            title=title,
            description=description,
            status=TaskStatus.PENDING.value,
            priority=priority.value,
            created_at=now,
            updated_at=now,
            tags=tags if tags else [],
            details={},
        )
        self._tasks.append(task)
        self._save_tasks()
        return task

    def update_task(
        self, task_id: str, status: Optional[TaskStatus] = None
    ) -> Optional[Task]:
        for task in self._tasks:
            if task.id == task_id:
                if status:
                    task.status = status.value
                task.updated_at = datetime.now().isoformat()
                self._save_tasks()
                return task
        return None

    def get_all_tasks(self) -> List[Task]:
        return self._tasks.copy()

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self._tasks if t.status == status.value]

    def get_stats(self) -> Dict:
        by_status = {}
        for task in self._tasks:
            by_status[task.status] = by_status.get(task.status, 0) + 1
        return {"total": len(self._tasks), "by_status": by_status}


_task_manager = None


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

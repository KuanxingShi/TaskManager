"""每日任务管理器"""

from datetime import date, datetime
from typing import List

from .models import DailyTasks, Priority, Task, TaskStatus
from .storage import load_daily, save_daily


class DailyManager:

    def __init__(self, target_date: date = None):
        self.date = target_date or date.today()
        self.daily = load_daily(self.date)

    def add_task(self, title: str, priority: Priority = Priority.URGENT_IMPORTANT,
                 tags: list = None, description: str = "") -> Task:
        task = Task(title=title, priority=priority,
                    tags=tags or [], description=description)
        self.daily.tasks.append(task)
        self._save()
        return task

    def delete_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.daily.tasks):
            if task.id == task_id:
                self.daily.tasks.pop(i)
                self._save()
                return True
        return False

    def start_task(self, task_id: str) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save()
        return True

    def complete_task(self, task_id: str) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.status = TaskStatus.DONE
        task.progress = 100
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save()
        return True

    def cancel_task(self, task_id: str) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.status = TaskStatus.CANCELLED
        self._save()
        return True

    def update_progress(self, task_id: str, progress: int) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.progress = max(0, min(100, progress))
        if task.progress > 0 and task.status == TaskStatus.TODO:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        if task.progress == 100:
            task.status = TaskStatus.DONE
            task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save()
        return True

    def add_note(self, task_id: str, note: str) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.notes = note
        self._save()
        return True

    def change_priority(self, task_id: str, priority: Priority) -> bool:
        task = self._find(task_id)
        if not task:
            return False
        task.priority = priority
        self._save()
        return True

    def reorder_tasks(self, task_ids: List[str]) -> bool:
        """按给定的 ID 顺序重新排列任务"""
        task_map = {t.id: t for t in self.daily.tasks}
        new_tasks = []
        for tid in task_ids:
            if tid in task_map:
                new_tasks.append(task_map.pop(tid))
        # 未在列表中的任务追加到末尾
        for t in self.daily.tasks:
            if t.id in task_map:
                new_tasks.append(t)
        self.daily.tasks = new_tasks
        self._save()
        return True

    def list_tasks(self):
        return self.daily.tasks

    def _find(self, task_id: str):
        for task in self.daily.tasks:
            if task.id == task_id:
                return task
        return None

    def _save(self):
        save_daily(self.daily)

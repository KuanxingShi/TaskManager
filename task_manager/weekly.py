"""每周任务管理器"""

from datetime import date, datetime
from typing import List

from .models import Priority, Task, TaskStatus, WeeklyGoal
from .storage import load_weekly, save_weekly


class WeeklyManager:

    def __init__(self, year: int = None, week: int = None):
        if year is None or week is None:
            iso = date.today().isocalendar()
            self.year = iso[0]
            self.week = iso[1]
        else:
            self.year = year
            self.week = week
        self.weekly = load_weekly(self.year, self.week)

    # ---------- 目标管理 ----------

    def add_goal(self, description: str) -> WeeklyGoal:
        goal = WeeklyGoal(description=description)
        self.weekly.goals.append(goal)
        self._save()
        return goal

    def complete_goal(self, index: int) -> bool:
        if 0 <= index < len(self.weekly.goals):
            self.weekly.goals[index].completed = True
            self._save()
            return True
        return False

    def uncomplete_goal(self, index: int) -> bool:
        if 0 <= index < len(self.weekly.goals):
            self.weekly.goals[index].completed = False
            self._save()
            return True
        return False

    def delete_goal(self, index: int) -> bool:
        if 0 <= index < len(self.weekly.goals):
            self.weekly.goals.pop(index)
            self._save()
            return True
        return False

    def list_goals(self):
        return self.weekly.goals

    # ---------- 任务管理 ----------

    def add_task(self, title: str, priority: Priority = Priority.URGENT_IMPORTANT,
                 tags: list = None, description: str = "",
                 due_date: str = "") -> Task:
        task = Task(title=title, priority=priority,
                    tags=tags or [], description=description,
                    due_date=due_date)
        self.weekly.tasks.append(task)
        self._save()
        return task

    def delete_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.weekly.tasks):
            if task.id == task_id:
                self.weekly.tasks.pop(i)
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
        task_map = {t.id: t for t in self.weekly.tasks}
        new_tasks = []
        for tid in task_ids:
            if tid in task_map:
                new_tasks.append(task_map.pop(tid))
        for t in self.weekly.tasks:
            if t.id in task_map:
                new_tasks.append(t)
        self.weekly.tasks = new_tasks
        self._save()
        return True

    def list_tasks(self):
        return self.weekly.tasks

    def _find(self, task_id: str):
        for task in self.weekly.tasks:
            if task.id == task_id:
                return task
        return None

    def _save(self):
        save_weekly(self.weekly)

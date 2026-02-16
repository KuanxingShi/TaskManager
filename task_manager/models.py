"""数据模型定义"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(Enum):
    URGENT_IMPORTANT = "紧急重要"
    URGENT_NOT_IMPORTANT = "紧急不重要"
    NOT_URGENT_IMPORTANT = "不紧急重要"
    NOT_URGENT_NOT_IMPORTANT = "不紧急不重要"


@dataclass
class Task:
    title: str
    id: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.URGENT_IMPORTANT
    tags: List[str] = field(default_factory=list)
    description: str = ""
    progress: int = 0
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    due_date: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")


@dataclass
class WeeklyGoal:
    description: str
    completed: bool = False


@dataclass
class DailyTasks:
    date: str  # YYYY-MM-DD
    tasks: List[Task] = field(default_factory=list)


@dataclass
class WeeklyTasks:
    year: int
    week: int
    start_date: str = ""
    end_date: str = ""
    goals: List[WeeklyGoal] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

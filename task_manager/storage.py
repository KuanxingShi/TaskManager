"""Markdown 存储层 - 负责任务的序列化/反序列化与文件读写"""

import os
import re
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from .models import (DailyTasks, Priority, Task, TaskStatus, WeeklyGoal,
                     WeeklyTasks)

# ---------- 路径配置 ----------

BASE_DIR = Path(os.environ.get("TASKMANAGER_DIR", "."))
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# ---------- 常量 ----------

STATUS_MARKERS = {
    TaskStatus.TODO: " ",
    TaskStatus.IN_PROGRESS: "~",
    TaskStatus.DONE: "x",
    TaskStatus.CANCELLED: "-",
}
MARKER_TO_STATUS = {v: k for k, v in STATUS_MARKERS.items()}

STATUS_NAMES = {
    TaskStatus.TODO: "待办",
    TaskStatus.IN_PROGRESS: "进行中",
    TaskStatus.DONE: "已完成",
    TaskStatus.CANCELLED: "已取消",
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

PRIORITY_MAP = {
    "紧急重要": Priority.URGENT_IMPORTANT,
    "紧急不重要": Priority.URGENT_NOT_IMPORTANT,
    "不紧急重要": Priority.NOT_URGENT_IMPORTANT,
    "不紧急不重要": Priority.NOT_URGENT_NOT_IMPORTANT,
    # 兼容旧格式
    "高": Priority.URGENT_IMPORTANT,
    "中": Priority.NOT_URGENT_IMPORTANT,
    "低": Priority.NOT_URGENT_NOT_IMPORTANT,
}

# ---------- 正则 ----------

# 兼容新旧格式: [分类:紧急重要] 或 [优先级:高]
TASK_RE = re.compile(
    r"^- \[([ x~\-])\] \*\*(.+?)\*\*\s*\[(?:分类|优先级):(.+?)\]\s*\[进度:(\d+)%\]"
)
META_RE = re.compile(r"^  - (.+?): (.+)$")
GOAL_RE = re.compile(r"^\d+\.\s*\[([ x])\]\s*(.+)$")


# ---------- 工具函数 ----------

def ensure_dirs():
    for d in [DATA_DIR / "daily", DATA_DIR / "weekly",
              REPORTS_DIR / "daily", REPORTS_DIR / "weekly"]:
        d.mkdir(parents=True, exist_ok=True)


def get_weekday_name(d: date) -> str:
    return WEEKDAY_NAMES[d.weekday()]


def get_week_range(year: int, week: int) -> Tuple[date, date]:
    """获取 ISO 周的起止日期 (周一 ~ 周日)"""
    jan4 = date(year, 1, 4)
    start = jan4 + timedelta(weeks=week - 1, days=-jan4.weekday())
    end = start + timedelta(days=6)
    return start, end


# ========== 任务序列化 ==========

def task_to_markdown(task: Task) -> str:
    marker = STATUS_MARKERS[task.status]
    status_label = STATUS_NAMES[task.status]
    lines = [
        f"- [{marker}] **{task.title}** [分类:{task.priority.value}] [进度:{task.progress}%]",
        f"  - ID: `{task.id}`",
        f"  - 状态: {status_label}",
    ]
    if task.tags:
        lines.append(f"  - 标签: {' '.join(f'`{t}`' for t in task.tags)}")
    if task.description:
        lines.append(f"  - 描述: {task.description}")
    if task.created_at:
        lines.append(f"  - 创建时间: {task.created_at}")
    if task.started_at:
        lines.append(f"  - 开始时间: {task.started_at}")
    if task.completed_at:
        lines.append(f"  - 完成时间: {task.completed_at}")
    if task.due_date:
        lines.append(f"  - 截止日期: {task.due_date}")
    if task.notes:
        lines.append(f"  - 备注: {task.notes}")
    return "\n".join(lines)


# ========== 任务反序列化 ==========

def parse_tasks_from_lines(lines: List[str]) -> List[Task]:
    tasks: List[Task] = []
    current_lines: List[str] = []

    for line in lines:
        if TASK_RE.match(line):
            if current_lines:
                t = _parse_single_task(current_lines)
                if t:
                    tasks.append(t)
            current_lines = [line]
        elif current_lines and META_RE.match(line):
            current_lines.append(line)
        else:
            if current_lines:
                t = _parse_single_task(current_lines)
                if t:
                    tasks.append(t)
                current_lines = []

    if current_lines:
        t = _parse_single_task(current_lines)
        if t:
            tasks.append(t)
    return tasks


def _parse_single_task(lines: List[str]) -> Optional[Task]:
    match = TASK_RE.match(lines[0])
    if not match:
        return None

    marker, title, priority_str, progress = match.groups()
    task = Task(
        title=title,
        status=MARKER_TO_STATUS.get(marker, TaskStatus.TODO),
        priority=PRIORITY_MAP.get(priority_str, Priority.URGENT_IMPORTANT),
        progress=int(progress),
    )

    for line in lines[1:]:
        meta = META_RE.match(line)
        if not meta:
            continue
        key, value = meta.groups()
        if key == "ID":
            task.id = value.strip("`")
        elif key == "标签":
            task.tags = [t.strip("`") for t in value.split() if t.strip("`")]
        elif key == "描述":
            task.description = value
        elif key == "创建时间":
            task.created_at = value
        elif key == "开始时间":
            task.started_at = value
        elif key == "完成时间":
            task.completed_at = value
        elif key == "截止日期":
            task.due_date = value
        elif key == "备注":
            task.notes = value
    return task


# ========== 统计辅助 ==========

def _build_stats_table(tasks: List[Task], extra_rows: List[Tuple[str, str]] = None) -> List[str]:
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    ip = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    todo = sum(1 for t in tasks if t.status == TaskStatus.TODO)
    cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
    rate = (done / total * 100) if total > 0 else 0

    rows = [
        "---", "",
        "## 统计", "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 总任务数 | {total} |",
        f"| 已完成 | {done} |",
        f"| 进行中 | {ip} |",
        f"| 待办 | {todo} |",
        f"| 已取消 | {cancelled} |",
        f"| 完成率 | {rate:.1f}% |",
    ]
    if extra_rows:
        for label, val in extra_rows:
            rows.append(f"| {label} | {val} |")
    rows.append("")
    return rows


# ========== 每日文件读写 ==========

def get_daily_path(d: date) -> Path:
    return DATA_DIR / "daily" / f"{d.isoformat()}.md"


def save_daily(daily: DailyTasks):
    ensure_dirs()
    d = date.fromisoformat(daily.date)
    weekday = get_weekday_name(d)

    # 按四象限分组
    sections = {p: [] for p in Priority}
    for task in daily.tasks:
        sections[task.priority].append(task)

    lines = [f"# 每日任务 - {daily.date} ({weekday})", ""]

    for priority in Priority:
        tasks = sections[priority]
        lines.append(f"## {priority.value}")
        lines.append("")
        if tasks:
            for task in tasks:
                lines.append(task_to_markdown(task))
                lines.append("")
        else:
            lines.append("*暂无任务*")
            lines.append("")

    lines.extend(_build_stats_table(daily.tasks))

    path = get_daily_path(d)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_daily(d: date) -> DailyTasks:
    path = get_daily_path(d)
    daily = DailyTasks(date=d.isoformat())
    if not path.exists():
        return daily
    content = path.read_text(encoding="utf-8")
    daily.tasks = parse_tasks_from_lines(content.split("\n"))
    return daily


# ========== 每周文件读写 ==========

def get_weekly_path(year: int, week: int) -> Path:
    return DATA_DIR / "weekly" / f"{year}-W{week:02d}.md"


def save_weekly(weekly: WeeklyTasks):
    ensure_dirs()
    start, end = get_week_range(weekly.year, weekly.week)

    # 按四象限分组
    sections = {p: [] for p in Priority}
    for task in weekly.tasks:
        sections[task.priority].append(task)

    lines = [
        f"# 每周任务 - {weekly.year}年第{weekly.week}周 "
        f"({start.strftime('%m/%d')} ~ {end.strftime('%m/%d')})",
        "",
        "## 本周目标", "",
    ]

    if weekly.goals:
        for i, g in enumerate(weekly.goals, 1):
            marker = "x" if g.completed else " "
            lines.append(f"{i}. [{marker}] {g.description}")
    else:
        lines.append("*暂无目标*")
    lines.append("")

    lines.extend(["## 任务列表", ""])

    for priority in Priority:
        tasks = sections[priority]
        lines.append(f"### {priority.value}")
        lines.append("")
        if tasks:
            for task in tasks:
                lines.append(task_to_markdown(task))
                lines.append("")
        else:
            lines.append("*暂无任务*")
            lines.append("")

    # 统计（含目标完成率）
    extra = []
    if weekly.goals:
        gd = sum(1 for g in weekly.goals if g.completed)
        gt = len(weekly.goals)
        extra.append(("目标完成率", f"{gd / gt * 100:.1f}% ({gd}/{gt})"))
    lines.extend(_build_stats_table(weekly.tasks, extra))

    path = get_weekly_path(weekly.year, weekly.week)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_weekly(year: int, week: int) -> WeeklyTasks:
    path = get_weekly_path(year, week)
    start, end = get_week_range(year, week)
    weekly = WeeklyTasks(
        year=year, week=week,
        start_date=start.strftime("%m/%d"),
        end_date=end.strftime("%m/%d"),
    )
    if not path.exists():
        return weekly

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # 解析目标
    in_goals = False
    for line in lines:
        if line.strip().startswith("## 本周目标"):
            in_goals = True
            continue
        if in_goals and line.startswith("## "):
            break
        if in_goals:
            m = GOAL_RE.match(line)
            if m:
                marker, desc = m.groups()
                weekly.goals.append(WeeklyGoal(description=desc, completed=(marker == "x")))

    weekly.tasks = parse_tasks_from_lines(lines)
    return weekly


# ========== 遗留任务加载 ==========

def _restore_task_status_at(task: Task, target_date_str: str):
    """将任务状态还原为目标日期时的状态（如果任务在目标日期之后才完成）"""
    if task.status == TaskStatus.DONE and task.completed_at:
        completed_date = task.completed_at[:10]
        if completed_date > target_date_str:
            if task.started_at and task.started_at[:10] <= target_date_str:
                task.status = TaskStatus.IN_PROGRESS
            else:
                task.status = TaskStatus.TODO
            task.completed_at = ""
            if task.progress == 100:
                task.progress = 0 if task.status == TaskStatus.TODO else 50
            return True
    return False


def load_daily_carryover(target_date: date, current_ids: set) -> List[Tuple[Task, str]]:
    """加载之前未完成的每日任务 (最多回溯30天)"""
    carryover = []
    seen = set(current_ids)
    d = target_date - timedelta(days=1)
    limit = target_date - timedelta(days=30)
    target_str = target_date.isoformat()
    while d >= limit:
        prev = load_daily(d)
        for task in prev.tasks:
            if task.id in seen:
                continue
            if task.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
                carryover.append((task, d.isoformat()))
                seen.add(task.id)
            elif _restore_task_status_at(task, target_str):
                carryover.append((task, d.isoformat()))
                seen.add(task.id)
        d -= timedelta(days=1)
    return carryover


def load_weekly_carryover(year: int, week: int, current_ids: set) -> List[Tuple[Task, str]]:
    """加载之前未完成的每周任务 (最多回溯4周)"""
    carryover = []
    seen = set(current_ids)
    _, target_end = get_week_range(year, week)
    target_end_str = target_end.isoformat()
    for i in range(1, 5):
        prev_week = week - i
        prev_year = year
        while prev_week < 1:
            prev_year -= 1
            dec28 = date(prev_year, 12, 28)
            max_week = dec28.isocalendar()[1]
            prev_week += max_week
        prev = load_weekly(prev_year, prev_week)
        source = f"{prev_year}-W{prev_week:02d}"
        for task in prev.tasks:
            if task.id in seen:
                continue
            if task.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
                carryover.append((task, source))
                seen.add(task.id)
            elif _restore_task_status_at(task, target_end_str):
                carryover.append((task, source))
                seen.add(task.id)
    return carryover


# ========== 报告文件路径 ==========

def get_daily_report_path(d: date) -> Path:
    return REPORTS_DIR / "daily" / f"{d.isoformat()}.md"


def get_weekly_report_path(year: int, week: int) -> Path:
    return REPORTS_DIR / "weekly" / f"{year}-W{week:02d}.md"


def save_report(path: Path, content: str):
    ensure_dirs()
    path.write_text(content, encoding="utf-8")

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskManager is a Markdown-based task management system with both CLI and web interfaces. Tasks are organized using the Eisenhower Matrix (four quadrants: 紧急重要, 紧急不重要, 不紧急重要, 不紧急不重要) and stored as Markdown files.

## Running the Application

### CLI Interface
```bash
# Daily tasks
python main.py daily add "任务名称" --priority 紧急重要 --tag 开发
python main.py daily list
python main.py daily start <ID>
python main.py daily done <ID>
python main.py daily progress <ID> 50

# Weekly tasks
python main.py weekly add "任务名称" --priority 紧急重要 --due 02/05
python main.py weekly list
python main.py weekly goal add "目标描述"

# Reports
python main.py report daily
python main.py report weekly
```

### Web Interface
```bash
python app.py
# Runs on http://127.0.0.1:5001
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Core Components

**Storage Layer (task_manager/storage.py)**
- Markdown-based persistence in `data/` directory
- Daily tasks: `data/daily/YYYY-MM-DD.md`
- Weekly tasks: `data/weekly/YYYY-WNN.md`
- Reports: `reports/daily/` and `reports/weekly/`
- Handles serialization/deserialization between Task objects and Markdown format
- Implements carryover logic: automatically loads incomplete tasks from previous periods (30 days for daily, 4 weeks for weekly)
- Special feature: `_restore_task_status_at()` restores task state to what it was at a specific date

**Data Models (task_manager/models.py)**
- `Task`: Core task entity with status (todo/in_progress/done/cancelled), priority (Eisenhower quadrants), progress percentage, timestamps
- `WeeklyGoal`: Simple goal tracker for weekly planning
- `DailyTasks` / `WeeklyTasks`: Containers for date/week-specific task collections

**Manager Classes**
- `DailyManager` (task_manager/daily.py): CRUD operations for daily tasks
- `WeeklyManager` (task_manager/weekly.py): CRUD + goal management for weekly tasks
- Both support task reordering via `reorder_tasks(task_ids)`

**Report Generator (task_manager/report.py)**
- Generates formatted daily/weekly reports with statistics
- Weekly reports include per-day breakdown of work volume
- Reports organized by Eisenhower quadrants

**Interfaces**
- `main.py`: Click-based CLI with nested command groups (daily/weekly/report)
- `app.py`: Flask REST API backend
- `templates/index.html` + `static/`: Single-page web UI

### Key Design Patterns

**Markdown as Database**: All tasks stored in human-readable Markdown files with specific format:
```markdown
- [x] **Task Title** [分类:紧急重要] [进度:100%]
  - ID: `abc12345`
  - 状态: 已完成
  - 标签: `开发` `bugfix`
```

**Quadrant Organization**: All list views group tasks by the four Eisenhower quadrants in priority order.

**Carryover System**: Incomplete tasks from previous periods are automatically loaded and displayed separately in the web UI, allowing users to continue or move them to current period.

**Environment Variable Support**: `TASKMANAGER_DIR` can override default base directory for data storage (defaults to current directory).

## File Structure

```
TaskManager/
├── main.py              # CLI entry point
├── app.py               # Flask web server
├── task_manager/        # Core package
│   ├── models.py        # Data classes
│   ├── storage.py       # Markdown I/O layer
│   ├── daily.py         # Daily task manager
│   ├── weekly.py        # Weekly task manager
│   └── report.py        # Report generator
├── templates/           # HTML templates
├── static/              # CSS/JS for web UI
├── data/                # Task storage (Markdown files)
│   ├── daily/
│   └── weekly/
└── reports/             # Generated reports
    ├── daily/
    └── weekly/
```

## Important Implementation Details

**Task IDs**: Auto-generated as 8-character hex strings (first 8 chars of UUID)

**Status Markers in Markdown**:
- ` ` = TODO
- `~` = IN_PROGRESS
- `x` = DONE
- `-` = CANCELLED

**Date Formats**:
- Dates: YYYY-MM-DD (ISO format)
- Weeks: YYYY-WNN (ISO week numbering)
- Timestamps: YYYY-MM-DD HH:MM

**Backward Compatibility**: Storage layer accepts both old format (优先级:高/中/低) and new format (分类:紧急重要/etc)

**Progress Auto-status**: Setting progress >0 auto-starts task (sets to IN_PROGRESS), progress=100 auto-completes task

# CLAUDE.md

## 项目简介

基于 Markdown 的任务管理系统，支持 CLI 和 Web 界面。任务按艾森豪威尔矩阵四象限组织，存储为 Markdown 文件。

## 运行

```bash
pip install -r requirements.txt
python main.py daily list        # CLI
python app.py                    # Web: http://127.0.0.1:5001
```

## 架构

| 文件 | 职责 |
|------|------|
| `task_manager/models.py` | 数据模型：Task、WeeklyGoal、DailyTasks、WeeklyTasks |
| `task_manager/storage.py` | Markdown 读写、历史任务结转（日任务30天、周任务4周） |
| `task_manager/daily.py` | 日任务 CRUD |
| `task_manager/weekly.py` | 周任务 CRUD + 目标管理 |
| `task_manager/report.py` | 报告生成 |
| `main.py` | Click CLI 入口 |
| `app.py` | Flask REST API |

## 数据存储

- 日任务：`data/daily/YYYY-MM-DD.md`
- 周任务：`data/weekly/YYYY-WNN.md`
- 报告：`reports/daily/`、`reports/weekly/`
- 环境变量 `TASKMANAGER_DIR` 可覆盖根目录

## Markdown 格式

```markdown
- [x] **任务标题** [分类:紧急重要] [进度:100%]
  - ID: `abc12345`
  - 状态: 已完成
  - 标签: `开发` `bugfix`
```

状态标记：` `=待办 `~`=进行中 `x`=已完成 `-`=已取消

## 关键规则

- Task ID：UUID 前8位十六进制
- 进度 >0 自动设为进行中，进度=100 自动完成
- 兼容旧格式（优先级:高/中/低）和新格式（分类:紧急重要/等）
- 四象限优先级：紧急重要 > 紧急不重要 > 不紧急重要 > 不紧急不重要

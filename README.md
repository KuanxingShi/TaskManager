# TaskManager

基于 Markdown 的任务管理系统，支持艾森豪威尔矩阵（四象限）任务分类，提供 CLI 和 Web 两种操作界面。

## 功能特性

- **四象限任务分类**：紧急重要 / 紧急不重要 / 不紧急重要 / 不紧急不重要
- **每日 & 每周任务管理**：独立的日/周视图与存储
- **任务结转**：未完成任务自动结转到下一周期
- **进度追踪**：支持百分比进度，自动更新任务状态
- **报告生成**：按四象限统计的日报 / 周报
- **Markdown 存储**：所有数据以人类可读的 Markdown 文件保存

## 安装

```bash
pip install -r requirements.txt
```

## 使用方式

### CLI 界面

```bash
# 每日任务
python main.py daily add "任务名称" --priority 紧急重要 --tag 开发
python main.py daily list
python main.py daily start <ID>
python main.py daily done <ID>
python main.py daily progress <ID> 50

# 每周任务
python main.py weekly add "任务名称" --priority 紧急重要 --due 02/05
python main.py weekly list
python main.py weekly goal add "目标描述"

# 报告
python main.py report daily
python main.py report weekly
```

### Web 界面

```bash
python app.py
```

访问 http://127.0.0.1:5001

## 项目结构

```
TaskManager/
├── main.py              # CLI 入口
├── app.py               # Flask Web 服务
├── task_manager/        # 核心模块
│   ├── models.py        # 数据模型
│   ├── storage.py       # Markdown 读写层
│   ├── daily.py         # 每日任务管理
│   ├── weekly.py        # 每周任务管理
│   └── report.py        # 报告生成器
├── templates/           # HTML 模板
├── static/              # CSS / JS
├── data/                # 任务数据（Markdown 文件）
└── reports/             # 生成的报告
```

## 数据格式

任务以 Markdown 格式存储：

```markdown
- [x] **任务标题** [分类:紧急重要] [进度:100%]
  - ID: `abc12345`
  - 状态: 已完成
  - 标签: `开发` `bugfix`
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TASKMANAGER_DIR` | 数据存储根目录 | 当前目录 |

## 依赖

- Python 3.8+
- Flask >= 3.0
- Click >= 8.0

"""TaskManager CLI - 基于 Markdown 的任务管理工具

用法:
    python main.py daily add "任务名称" --priority 紧急重要 --tag 开发 --desc "描述"
    python main.py daily list
    python main.py daily start <ID>
    python main.py daily done <ID>
    python main.py daily progress <ID> 50
    python main.py daily delete <ID>
    python main.py daily note <ID> "备注"

    python main.py weekly add "任务名称" --priority 紧急重要 --due 02/05
    python main.py weekly list
    python main.py weekly goal add "目标描述"
    python main.py weekly goal done 1
    python main.py weekly goal list

    python main.py report daily
    python main.py report weekly
    python main.py report monthly
    python main.py report monthly --month 2026-02
    python main.py report quarterly
    python main.py report quarterly --quarter 2026-Q1
    python main.py report range --start 2026-01-01 --end 2026-01-31
"""

import click
from datetime import date

from task_manager.models import Priority, TaskStatus
from task_manager.daily import DailyManager
from task_manager.weekly import WeeklyManager
from task_manager.report import ReportGenerator

PRIORITY_CHOICES = ["紧急重要", "紧急不重要", "不紧急重要", "不紧急不重要"]
PRIORITY_MAP = {
    "紧急重要": Priority.URGENT_IMPORTANT,
    "紧急不重要": Priority.URGENT_NOT_IMPORTANT,
    "不紧急重要": Priority.NOT_URGENT_IMPORTANT,
    "不紧急不重要": Priority.NOT_URGENT_NOT_IMPORTANT,
}
STATUS_DISPLAY = {
    TaskStatus.TODO: "待办",
    TaskStatus.IN_PROGRESS: "进行中",
    TaskStatus.DONE: "已完成",
    TaskStatus.CANCELLED: "已取消",
}


def _print_task(task):
    status = STATUS_DISPLAY[task.status]
    line = f"  [{task.id}] {task.title}  状态:{status}  分类:{task.priority.value}  进度:{task.progress}%"
    if task.tags:
        line += f"  标签:{','.join(task.tags)}"
    if task.notes:
        line += f"\n           备注: {task.notes}"
    click.echo(line)


# ======================== 根命令 ========================

@click.group()
@click.version_option("1.1.0", prog_name="TaskManager")
def cli():
    """TaskManager - 基于 Markdown 的任务管理工具 (四象限版)"""
    pass


# ======================== daily 命令组 ========================

@cli.group()
def daily():
    """每日任务管理"""
    pass


@daily.command("add")
@click.argument("title")
@click.option("--priority", "-p", type=click.Choice(PRIORITY_CHOICES), default="紧急重要", help="四象限分类")
@click.option("--tag", "-t", multiple=True, help="标签 (可多次使用)")
@click.option("--desc", "-d", default="", help="任务描述")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD, 默认今天")
def daily_add(title, priority, tag, desc, target_date):
    """添加每日任务"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    task = mgr.add_task(title, PRIORITY_MAP[priority], list(tag), desc)
    click.echo(f"+ 已添加: {task.title}  (ID: {task.id})  分类: {priority}")


@daily.command("list")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD, 默认今天")
def daily_list(target_date):
    """列出每日任务 (按四象限分组)"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    tasks = mgr.list_tasks()
    if not tasks:
        click.echo(f"  {d.isoformat()} 暂无任务")
        return
    click.echo(f"\n  === 每日任务 - {d.isoformat()} ===\n")
    for priority in Priority:
        ptasks = [t for t in tasks if t.priority == priority]
        click.echo(f"  --- {priority.value} ({len(ptasks)}) ---")
        if ptasks:
            for task in ptasks:
                _print_task(task)
        else:
            click.echo("    (空)")
        click.echo()


@daily.command("start")
@click.argument("task_id")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_start(task_id, target_date):
    """开始任务 (标记为进行中)"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.start_task(task_id):
        click.echo(f"~ 任务 {task_id} 已开始")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@daily.command("done")
@click.argument("task_id")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_done(task_id, target_date):
    """完成任务"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.complete_task(task_id):
        click.echo(f"v 任务 {task_id} 已完成")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@daily.command("cancel")
@click.argument("task_id")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_cancel(task_id, target_date):
    """取消任务"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.cancel_task(task_id):
        click.echo(f"- 任务 {task_id} 已取消")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@daily.command("progress")
@click.argument("task_id")
@click.argument("value", type=int)
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_progress(task_id, value, target_date):
    """更新任务进度 (0-100)"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.update_progress(task_id, value):
        click.echo(f"~ 任务 {task_id} 进度已更新为 {value}%")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@daily.command("note")
@click.argument("task_id")
@click.argument("content")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_note(task_id, content, target_date):
    """添加任务备注"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.add_note(task_id, content):
        click.echo(f"# 任务 {task_id} 备注已更新")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@daily.command("delete")
@click.argument("task_id")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD")
def daily_delete(task_id, target_date):
    """删除任务"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    mgr = DailyManager(d)
    if mgr.delete_task(task_id):
        click.echo(f"x 任务 {task_id} 已删除")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


# ======================== weekly 命令组 ========================

@cli.group()
def weekly():
    """每周任务管理"""
    pass


def _parse_week_option(week_str):
    """解析 YYYY-WNN 格式, 返回 (year, week)"""
    if week_str:
        parts = week_str.split("-W")
        return int(parts[0]), int(parts[1])
    return None, None


@weekly.command("add")
@click.argument("title")
@click.option("--priority", "-p", type=click.Choice(PRIORITY_CHOICES), default="紧急重要", help="四象限分类")
@click.option("--tag", "-t", multiple=True, help="标签")
@click.option("--desc", "-d", default="", help="任务描述")
@click.option("--due", default="", help="截止日期 (如 02/05)")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN, 默认本周")
def weekly_add(title, priority, tag, desc, due, week_str):
    """添加每周任务"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    task = mgr.add_task(title, PRIORITY_MAP[priority], list(tag), desc, due)
    click.echo(f"+ 已添加: {task.title}  (ID: {task.id})  分类: {priority}")


@weekly.command("list")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN, 默认本周")
def weekly_list(week_str):
    """列出每周任务 (按四象限分组)"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)

    # 打印目标
    goals = mgr.list_goals()
    click.echo(f"\n  === {mgr.year}年第{mgr.week}周 ===\n")
    if goals:
        click.echo("  本周目标:")
        for i, g in enumerate(goals):
            mark = "x" if g.completed else " "
            click.echo(f"    {i + 1}. [{mark}] {g.description}")
        click.echo()

    tasks = mgr.list_tasks()
    if not tasks:
        click.echo("  暂无任务")
        return
    click.echo("  任务列表:")
    for priority in Priority:
        ptasks = [t for t in tasks if t.priority == priority]
        click.echo(f"  --- {priority.value} ({len(ptasks)}) ---")
        if ptasks:
            for task in ptasks:
                _print_task(task)
        else:
            click.echo("    (空)")
        click.echo()


@weekly.command("start")
@click.argument("task_id")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_start(task_id, week_str):
    """开始每周任务"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.start_task(task_id):
        click.echo(f"~ 任务 {task_id} 已开始")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@weekly.command("done")
@click.argument("task_id")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_done(task_id, week_str):
    """完成每周任务"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.complete_task(task_id):
        click.echo(f"v 任务 {task_id} 已完成")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@weekly.command("cancel")
@click.argument("task_id")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_cancel(task_id, week_str):
    """取消每周任务"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.cancel_task(task_id):
        click.echo(f"- 任务 {task_id} 已取消")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@weekly.command("progress")
@click.argument("task_id")
@click.argument("value", type=int)
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_progress(task_id, value, week_str):
    """更新每周任务进度"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.update_progress(task_id, value):
        click.echo(f"~ 任务 {task_id} 进度已更新为 {value}%")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@weekly.command("note")
@click.argument("task_id")
@click.argument("content")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_note(task_id, content, week_str):
    """添加每周任务备注"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.add_note(task_id, content):
        click.echo(f"# 任务 {task_id} 备注已更新")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


@weekly.command("delete")
@click.argument("task_id")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def weekly_delete(task_id, week_str):
    """删除每周任务"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.delete_task(task_id):
        click.echo(f"x 任务 {task_id} 已删除")
    else:
        click.echo(f"! 未找到任务 {task_id}", err=True)


# ---- weekly goal 子命令组 ----

@weekly.group("goal")
def weekly_goal():
    """每周目标管理"""
    pass


@weekly_goal.command("add")
@click.argument("description")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def goal_add(description, week_str):
    """添加本周目标"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    mgr.add_goal(description)
    click.echo(f"+ 已添加目标: {description}")


@weekly_goal.command("done")
@click.argument("index", type=int)
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def goal_done(index, week_str):
    """标记目标完成 (序号从 1 开始)"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.complete_goal(index - 1):
        click.echo(f"v 目标 {index} 已完成")
    else:
        click.echo(f"! 目标序号 {index} 无效", err=True)


@weekly_goal.command("undo")
@click.argument("index", type=int)
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def goal_undo(index, week_str):
    """取消目标完成状态"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.uncomplete_goal(index - 1):
        click.echo(f"~ 目标 {index} 已标记为未完成")
    else:
        click.echo(f"! 目标序号 {index} 无效", err=True)


@weekly_goal.command("delete")
@click.argument("index", type=int)
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def goal_delete(index, week_str):
    """删除目标 (序号从 1 开始)"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    if mgr.delete_goal(index - 1):
        click.echo(f"x 目标 {index} 已删除")
    else:
        click.echo(f"! 目标序号 {index} 无效", err=True)


@weekly_goal.command("list")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN")
def goal_list(week_str):
    """列出本周目标"""
    year, week = _parse_week_option(week_str)
    mgr = WeeklyManager(year, week)
    goals = mgr.list_goals()
    if not goals:
        click.echo("  暂无本周目标")
        return
    click.echo(f"\n  === {mgr.year}年第{mgr.week}周 目标 ===\n")
    for i, g in enumerate(goals):
        mark = "x" if g.completed else " "
        click.echo(f"    {i + 1}. [{mark}] {g.description}")
    click.echo()


# ======================== report 命令组 ========================

@cli.group()
def report():
    """生成日报 / 周报"""
    pass


@report.command("daily")
@click.option("--date", "target_date", default=None, help="日期 YYYY-MM-DD, 默认今天")
def report_daily(target_date):
    """生成日报"""
    d = date.fromisoformat(target_date) if target_date else date.today()
    gen = ReportGenerator()
    content = gen.generate_daily_report(d)
    click.echo(content)
    click.echo(f"\n报告已保存至 reports/daily/{d.isoformat()}.md")


@report.command("weekly")
@click.option("--week", "week_str", default=None, help="周 YYYY-WNN, 默认本周")
def report_weekly(week_str):
    """生成周报"""
    year, week = _parse_week_option(week_str)
    if year is None:
        iso = date.today().isocalendar()
        year, week = iso[0], iso[1]
    gen = ReportGenerator()
    content = gen.generate_weekly_report(year, week)
    click.echo(content)
    click.echo(f"\n报告已保存至 reports/weekly/{year}-W{week:02d}.md")


@report.command("monthly")
@click.option("--month", "month_str", default=None,
              help="月份 YYYY-MM, 默认本月")
def report_monthly(month_str):
    """生成月报"""
    if month_str:
        parts = month_str.split("-")
        year, month = int(parts[0]), int(parts[1])
    else:
        today = date.today()
        year, month = today.year, today.month
    gen = ReportGenerator()
    content = gen.generate_monthly_report(year, month)
    click.echo(content)
    click.echo(f"\n报告已保存至 reports/monthly/{year}-{month:02d}.md")


@report.command("quarterly")
@click.option("--quarter", "quarter_str", default=None,
              help="季度 YYYY-QN (如 2026-Q1), 默认本季度")
def report_quarterly(quarter_str):
    """生成季报"""
    if quarter_str:
        parts = quarter_str.split("-Q")
        year, quarter = int(parts[0]), int(parts[1])
    else:
        today = date.today()
        year = today.year
        quarter = (today.month - 1) // 3 + 1
    gen = ReportGenerator()
    content = gen.generate_quarterly_report(year, quarter)
    click.echo(content)
    click.echo(f"\n报告已保存至 reports/quarterly/{year}-Q{quarter}.md")


@report.command("range")
@click.option("--start", "start_str", required=True,
              help="开始日期 YYYY-MM-DD")
@click.option("--end", "end_str", required=True,
              help="结束日期 YYYY-MM-DD")
def report_range(start_str, end_str):
    """生成自定义区间报告"""
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if start > end:
        click.echo("错误: 开始日期不能晚于结束日期", err=True)
        raise SystemExit(1)
    gen = ReportGenerator()
    content = gen.generate_range_report(start, end)
    click.echo(content)
    click.echo(f"\n报告已保存至 reports/range/{start_str}_{end_str}.md")


# ======================== 入口 ========================

if __name__ == "__main__":
    cli()

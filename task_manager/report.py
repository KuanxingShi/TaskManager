"""日报 / 周报 / 月报 / 季报 / 自定义区间报告生成器"""

import calendar
from datetime import date, timedelta

from .models import Priority, TaskStatus
from .storage import (get_daily_report_path, get_monthly_report_path,
                      get_quarterly_report_path, get_range_report_path,
                      get_week_range, get_weekday_name, get_weekly_report_path,
                      load_daily, load_weekly, save_report)


class ReportGenerator:

    # ==================== 日报 ====================

    def generate_daily_report(self, target_date: date = None) -> str:
        d = target_date or date.today()
        daily = load_daily(d)
        weekday = get_weekday_name(d)
        tasks = daily.tasks

        done = [t for t in tasks if t.status == TaskStatus.DONE]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        todo = [t for t in tasks if t.status == TaskStatus.TODO]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]

        total = len(tasks)
        rate = (len(done) / total * 100) if total > 0 else 0

        lines = [
            f"# 日报 - {d.isoformat()} ({weekday})",
            "",
            "## 今日概览", "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总任务数 | {total} |",
            f"| 已完成 | {len(done)} |",
            f"| 进行中 | {len(in_progress)} |",
            f"| 待办 | {len(todo)} |",
            f"| 已取消 | {len(cancelled)} |",
            f"| 完成率 | {rate:.1f}% |",
            "",
        ]

        # -- 按四象限分组展示 --
        lines.extend(["## 四象限任务分布", ""])
        for priority in Priority:
            ptasks = [t for t in tasks if t.priority == priority]
            lines.append(f"### {priority.value} ({len(ptasks)})")
            lines.append("")
            if ptasks:
                for i, t in enumerate(ptasks, 1):
                    status_label = {"done": "已完成", "in_progress": "进行中",
                                    "todo": "待办", "cancelled": "已取消"}[t.status.value]
                    lines.append(f"{i}. **{t.title}** [{status_label}] [进度:{t.progress}%]")
                    if t.notes:
                        lines.append(f"   - 备注: {t.notes}")
            else:
                lines.append("*暂无任务*")
            lines.append("")

        # -- 已完成 --
        lines.extend(["## 今日完成", ""])
        if done:
            for i, t in enumerate(done, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.completed_at:
                    lines.append(f"   - 完成时间: {t.completed_at}")
                if t.notes:
                    lines.append(f"   - 备注: {t.notes}")
        else:
            lines.append("*暂无完成任务*")
        lines.append("")

        # -- 进行中 --
        lines.extend(["## 进行中", ""])
        if in_progress:
            for i, t in enumerate(in_progress, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}] [进度:{t.progress}%]")
                if t.notes:
                    lines.append(f"   - 当前进展: {t.notes}")
                if t.description:
                    lines.append(f"   - 描述: {t.description}")
        else:
            lines.append("*暂无进行中任务*")
        lines.append("")

        # -- 待办 --
        lines.extend(["## 待办事项", ""])
        if todo:
            for i, t in enumerate(todo, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.description:
                    lines.append(f"   - 描述: {t.description}")
        else:
            lines.append("*暂无待办任务*")
        lines.append("")

        content = "\n".join(lines)
        save_report(get_daily_report_path(d), content)
        return content

    # ==================== 周报 ====================

    def generate_weekly_report(self, year: int = None, week: int = None) -> str:
        if year is None or week is None:
            iso = date.today().isocalendar()
            year, week = iso[0], iso[1]

        weekly = load_weekly(year, week)
        start, end = get_week_range(year, week)
        tasks = weekly.tasks

        done = [t for t in tasks if t.status == TaskStatus.DONE]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        todo = [t for t in tasks if t.status == TaskStatus.TODO]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]

        total = len(tasks)
        rate = (len(done) / total * 100) if total > 0 else 0

        lines = [
            f"# 周报 - {year}年第{week}周 "
            f"({start.strftime('%m/%d')} ~ {end.strftime('%m/%d')})",
            "",
            "## 本周概览", "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总任务数 | {total} |",
            f"| 已完成 | {len(done)} |",
            f"| 进行中 | {len(in_progress)} |",
            f"| 待办 | {len(todo)} |",
            f"| 已取消 | {len(cancelled)} |",
            f"| 任务完成率 | {rate:.1f}% |",
            "",
        ]

        # -- 目标 --
        if weekly.goals:
            lines.extend(["## 目标完成情况", ""])
            goals_done = 0
            for i, g in enumerate(weekly.goals, 1):
                status_text = "[已完成]" if g.completed else "[未完成]"
                lines.append(f"{i}. {status_text} {g.description}")
                if g.completed:
                    goals_done += 1
            goals_rate = goals_done / len(weekly.goals) * 100
            lines.extend([
                "",
                f"目标完成率: {goals_rate:.1f}% ({goals_done}/{len(weekly.goals)})",
                "",
            ])

        # -- 按四象限分组展示 --
        lines.extend(["## 四象限任务分布", ""])
        for priority in Priority:
            ptasks = [t for t in tasks if t.priority == priority]
            lines.append(f"### {priority.value} ({len(ptasks)})")
            lines.append("")
            if ptasks:
                for i, t in enumerate(ptasks, 1):
                    status_label = {"done": "已完成", "in_progress": "进行中",
                                    "todo": "待办", "cancelled": "已取消"}[t.status.value]
                    lines.append(f"{i}. **{t.title}** [{status_label}] [进度:{t.progress}%]")
                    if t.notes:
                        lines.append(f"   - 备注: {t.notes}")
            else:
                lines.append("*暂无任务*")
            lines.append("")

        # -- 已完成任务 --
        lines.extend(["## 已完成任务", ""])
        if done:
            for i, t in enumerate(done, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.completed_at:
                    lines.append(f"   - 完成时间: {t.completed_at}")
                if t.notes:
                    lines.append(f"   - 备注: {t.notes}")
        else:
            lines.append("*暂无完成任务*")
        lines.append("")

        # -- 进行中任务 --
        lines.extend(["## 进行中任务", ""])
        if in_progress:
            for i, t in enumerate(in_progress, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}] [进度:{t.progress}%]")
                if t.notes:
                    lines.append(f"   - 当前进展: {t.notes}")
        else:
            lines.append("*暂无进行中任务*")
        lines.append("")

        # -- 待办任务 --
        lines.extend(["## 待办任务", ""])
        if todo:
            for i, t in enumerate(todo, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.description:
                    lines.append(f"   - 描述: {t.description}")
        else:
            lines.append("*暂无待办任务*")
        lines.append("")

        # -- 每日工作量 --
        lines.extend(["## 每日工作量", ""])
        lines.append("| 日期 | 总数 | 完成 | 进行中 | 待办 |")
        lines.append("|------|------|------|--------|------|")
        current = start
        while current <= end and current <= date.today():
            dl = load_daily(current)
            d_done = sum(1 for t in dl.tasks if t.status == TaskStatus.DONE)
            d_ip = sum(1 for t in dl.tasks if t.status == TaskStatus.IN_PROGRESS)
            d_todo = sum(1 for t in dl.tasks if t.status == TaskStatus.TODO)
            d_total = len(dl.tasks)
            wd = get_weekday_name(current)
            lines.append(
                f"| {current.strftime('%m/%d')} ({wd}) "
                f"| {d_total} | {d_done} | {d_ip} | {d_todo} |"
            )
            current += timedelta(days=1)
        lines.append("")

        content = "\n".join(lines)
        save_report(get_weekly_report_path(year, week), content)
        return content

    # ==================== 自定义区间报告 ====================

    def generate_range_report(self, start: date, end: date,
                               report_title: str = None,
                               save_path=None) -> str:
        """汇总 start ~ end 每日任务文件，生成区间报告。

        相同任务 ID 以最后出现的状态为准（即最新状态）。
        """
        tasks_by_id: dict = {}
        current = start
        while current <= end:
            daily = load_daily(current)
            for t in daily.tasks:
                tasks_by_id[t.id] = t
            current += timedelta(days=1)

        tasks = list(tasks_by_id.values())

        done = [t for t in tasks if t.status == TaskStatus.DONE]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        todo = [t for t in tasks if t.status == TaskStatus.TODO]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]

        total = len(tasks)
        rate = (len(done) / total * 100) if total > 0 else 0

        header = report_title or (
            f"自定义报告 ({start.isoformat()} ~ {end.isoformat()})"
        )

        lines = [
            f"# {header}",
            "",
            "## 概览", "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 统计周期 | {start.isoformat()} ~ {end.isoformat()} |",
            f"| 总任务数 | {total} |",
            f"| 已完成 | {len(done)} |",
            f"| 进行中 | {len(in_progress)} |",
            f"| 待办 | {len(todo)} |",
            f"| 已取消 | {len(cancelled)} |",
            f"| 完成率 | {rate:.1f}% |",
            "",
        ]

        # -- 按四象限分组展示 --
        lines.extend(["## 四象限任务分布", ""])
        for priority in Priority:
            ptasks = [t for t in tasks if t.priority == priority]
            lines.append(f"### {priority.value} ({len(ptasks)})")
            lines.append("")
            if ptasks:
                for i, t in enumerate(ptasks, 1):
                    status_label = {"done": "已完成", "in_progress": "进行中",
                                    "todo": "待办", "cancelled": "已取消"}[t.status.value]
                    lines.append(f"{i}. **{t.title}** [{status_label}] [进度:{t.progress}%]")
                    if t.notes:
                        lines.append(f"   - 备注: {t.notes}")
            else:
                lines.append("*暂无任务*")
            lines.append("")

        # -- 已完成任务 --
        lines.extend(["## 已完成任务", ""])
        if done:
            for i, t in enumerate(done, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.completed_at:
                    lines.append(f"   - 完成时间: {t.completed_at}")
                if t.notes:
                    lines.append(f"   - 备注: {t.notes}")
        else:
            lines.append("*暂无完成任务*")
        lines.append("")

        # -- 进行中任务 --
        lines.extend(["## 进行中任务", ""])
        if in_progress:
            for i, t in enumerate(in_progress, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}] [进度:{t.progress}%]")
                if t.notes:
                    lines.append(f"   - 当前进展: {t.notes}")
        else:
            lines.append("*暂无进行中任务*")
        lines.append("")

        # -- 待办任务 --
        lines.extend(["## 待办任务", ""])
        if todo:
            for i, t in enumerate(todo, 1):
                lines.append(f"{i}. **{t.title}** [分类:{t.priority.value}]")
                if t.description:
                    lines.append(f"   - 描述: {t.description}")
        else:
            lines.append("*暂无待办任务*")
        lines.append("")

        # -- 每日工作量 --
        lines.extend(["## 每日工作量", ""])
        lines.append("| 日期 | 总数 | 完成 | 进行中 | 待办 |")
        lines.append("|------|------|------|--------|------|")
        current = start
        today = date.today()
        while current <= end and current <= today:
            dl = load_daily(current)
            d_done = sum(1 for t in dl.tasks if t.status == TaskStatus.DONE)
            d_ip = sum(1 for t in dl.tasks if t.status == TaskStatus.IN_PROGRESS)
            d_todo = sum(1 for t in dl.tasks if t.status == TaskStatus.TODO)
            d_total = len(dl.tasks)
            wd = get_weekday_name(current)
            lines.append(
                f"| {current.strftime('%m/%d')} ({wd}) "
                f"| {d_total} | {d_done} | {d_ip} | {d_todo} |"
            )
            current += timedelta(days=1)
        lines.append("")

        content = "\n".join(lines)
        path = save_path or get_range_report_path(start, end)
        save_report(path, content)
        return content

    # ==================== 月报 ====================

    def generate_monthly_report(self, year: int = None, month: int = None) -> str:
        today = date.today()
        year = year or today.year
        month = month or today.month
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        month_name = f"{year}年{month}月"
        title = f"月报 - {month_name}"
        path = get_monthly_report_path(year, month)
        return self.generate_range_report(start, end, title, save_path=path)

    # ==================== 季报 ====================

    def generate_quarterly_report(self, year: int = None,
                                   quarter: int = None) -> str:
        today = date.today()
        year = year or today.year
        quarter = quarter or ((today.month - 1) // 3 + 1)
        first_month = (quarter - 1) * 3 + 1
        last_month = first_month + 2
        start = date(year, first_month, 1)
        end = date(year, last_month, calendar.monthrange(year, last_month)[1])
        title = f"季报 - {year}年Q{quarter} ({start.strftime('%m/%d')} ~ {end.strftime('%m/%d')})"
        path = get_quarterly_report_path(year, quarter)
        return self.generate_range_report(start, end, title, save_path=path)

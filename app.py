"""TaskManager Web - Flask 后端"""

from datetime import date

from flask import Flask, jsonify, render_template, request

from task_manager.daily import DailyManager
from task_manager.models import Priority
from task_manager.report import ReportGenerator
from task_manager.weekly import WeeklyManager
from task_manager.storage import load_daily_carryover, load_weekly_carryover

app = Flask(__name__)

PRIORITY_MAP = {
    "紧急重要": Priority.URGENT_IMPORTANT,
    "紧急不重要": Priority.URGENT_NOT_IMPORTANT,
    "不紧急重要": Priority.NOT_URGENT_IMPORTANT,
    "不紧急不重要": Priority.NOT_URGENT_NOT_IMPORTANT,
    # 兼容旧值
    "高": Priority.URGENT_IMPORTANT,
    "中": Priority.NOT_URGENT_IMPORTANT,
    "低": Priority.NOT_URGENT_NOT_IMPORTANT,
}


def _task_dict(t):
    return {
        "id": t.id, "title": t.title, "status": t.status.value,
        "priority": t.priority.value, "tags": t.tags,
        "description": t.description, "progress": t.progress,
        "created_at": t.created_at, "started_at": t.started_at,
        "completed_at": t.completed_at, "due_date": t.due_date,
        "notes": t.notes,
    }


def _carryover_task_dict(t, source):
    d = _task_dict(t)
    d["carryover"] = True
    d["source"] = source
    return d


def _goal_dict(g, i):
    return {"index": i, "description": g.description, "completed": g.completed}


# ==================== 页面 ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== Daily API ====================

@app.route("/api/daily")
def daily_list():
    d = request.args.get("date", date.today().isoformat())
    target = date.fromisoformat(d)
    mgr = DailyManager(target)
    tasks = [_task_dict(t) for t in mgr.list_tasks()]
    # 遗留任务
    current_ids = {t.id for t in mgr.list_tasks()}
    carryover = load_daily_carryover(target, current_ids)
    carryover_tasks = [_carryover_task_dict(t, src) for t, src in carryover]
    return jsonify({"date": d, "tasks": tasks, "carryover": carryover_tasks})


@app.route("/api/daily", methods=["POST"])
def daily_add():
    data = request.json
    d = date.fromisoformat(data.get("date", date.today().isoformat()))
    mgr = DailyManager(d)
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    task = mgr.add_task(
        title=data["title"],
        priority=PRIORITY_MAP.get(data.get("priority", "紧急重要"), Priority.URGENT_IMPORTANT),
        tags=tags,
        description=data.get("description", ""),
    )
    return jsonify(_task_dict(task)), 201


@app.route("/api/daily/<task_id>", methods=["PUT"])
def daily_update(task_id):
    data = request.json
    d = date.fromisoformat(data.get("date", date.today().isoformat()))
    mgr = DailyManager(d)
    action = data.get("action")
    ok = False
    if action == "start":
        ok = mgr.start_task(task_id)
    elif action == "done":
        ok = mgr.complete_task(task_id)
    elif action == "cancel":
        ok = mgr.cancel_task(task_id)
    elif action == "progress":
        ok = mgr.update_progress(task_id, int(data.get("value", 0)))
    elif action == "note":
        ok = mgr.add_note(task_id, data.get("value", ""))
    elif action == "priority":
        new_priority = PRIORITY_MAP.get(data.get("value"), None)
        if new_priority:
            ok = mgr.change_priority(task_id, new_priority)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "未找到任务"}), 404


@app.route("/api/daily/<task_id>", methods=["DELETE"])
def daily_delete(task_id):
    d = date.fromisoformat(request.args.get("date", date.today().isoformat()))
    mgr = DailyManager(d)
    if mgr.delete_task(task_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "未找到任务"}), 404


@app.route("/api/daily/reorder", methods=["PUT"])
def daily_reorder():
    data = request.json
    d = date.fromisoformat(data.get("date", date.today().isoformat()))
    mgr = DailyManager(d)
    order = data.get("order", [])
    mgr.reorder_tasks(order)
    return jsonify({"ok": True})


# ==================== Weekly API ====================

@app.route("/api/weekly")
def weekly_list():
    year = request.args.get("year", type=int)
    week = request.args.get("week", type=int)
    mgr = WeeklyManager(year, week)
    tasks = [_task_dict(t) for t in mgr.list_tasks()]
    # 遗留任务
    current_ids = {t.id for t in mgr.list_tasks()}
    carryover = load_weekly_carryover(mgr.year, mgr.week, current_ids)
    carryover_tasks = [_carryover_task_dict(t, src) for t, src in carryover]
    return jsonify({
        "year": mgr.year, "week": mgr.week,
        "goals": [_goal_dict(g, i) for i, g in enumerate(mgr.list_goals())],
        "tasks": tasks, "carryover": carryover_tasks,
    })


@app.route("/api/weekly", methods=["POST"])
def weekly_add():
    data = request.json
    # [AI] 2026-02-21 kxshi: 添加类型转换异常处理，防止无效输入导致500错误
    try:
        year = int(data.get("year")) if data.get("year") is not None else None
        week = int(data.get("week")) if data.get("week") is not None else None
    except (ValueError, TypeError):
        return jsonify({"error": "year 和 week 必须为有效整数"}), 400
    mgr = WeeklyManager(year, week)
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    task = mgr.add_task(
        title=data["title"],
        priority=PRIORITY_MAP.get(data.get("priority", "紧急重要"), Priority.URGENT_IMPORTANT),
        tags=tags,
        description=data.get("description", ""),
        due_date=data.get("due_date", ""),
    )
    return jsonify(_task_dict(task)), 201


@app.route("/api/weekly/<task_id>", methods=["PUT"])
def weekly_update(task_id):
    data = request.json
    mgr = WeeklyManager(data.get("year"), data.get("week"))
    action = data.get("action")
    ok = False
    if action == "start":
        ok = mgr.start_task(task_id)
    elif action == "done":
        ok = mgr.complete_task(task_id)
    elif action == "cancel":
        ok = mgr.cancel_task(task_id)
    elif action == "progress":
        ok = mgr.update_progress(task_id, int(data.get("value", 0)))
    elif action == "note":
        ok = mgr.add_note(task_id, data.get("value", ""))
    elif action == "priority":
        new_priority = PRIORITY_MAP.get(data.get("value"), None)
        if new_priority:
            ok = mgr.change_priority(task_id, new_priority)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "未找到任务"}), 404


@app.route("/api/weekly/<task_id>", methods=["DELETE"])
def weekly_delete(task_id):
    year = request.args.get("year", type=int)
    week = request.args.get("week", type=int)
    mgr = WeeklyManager(year, week)
    if mgr.delete_task(task_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "未找到任务"}), 404


@app.route("/api/weekly/reorder", methods=["PUT"])
def weekly_reorder():
    data = request.json
    mgr = WeeklyManager(data.get("year"), data.get("week"))
    order = data.get("order", [])
    mgr.reorder_tasks(order)
    return jsonify({"ok": True})


# ---- Goals ----

@app.route("/api/weekly/goals", methods=["POST"])
def weekly_goal_add():
    data = request.json
    mgr = WeeklyManager(data.get("year"), data.get("week"))
    mgr.add_goal(data["description"])
    return jsonify({"ok": True}), 201


@app.route("/api/weekly/goals/<int:idx>", methods=["PUT"])
def weekly_goal_update(idx):
    data = request.json
    mgr = WeeklyManager(data.get("year"), data.get("week"))
    action = data.get("action", "done")
    if action == "done":
        ok = mgr.complete_goal(idx)
    else:
        ok = mgr.uncomplete_goal(idx)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404


@app.route("/api/weekly/goals/<int:idx>", methods=["DELETE"])
def weekly_goal_delete(idx):
    year = request.args.get("year", type=int)
    week = request.args.get("week", type=int)
    mgr = WeeklyManager(year, week)
    if mgr.delete_goal(idx):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404


# ==================== Report API ====================

@app.route("/api/report/daily")
def report_daily():
    d = date.fromisoformat(request.args.get("date", date.today().isoformat()))
    gen = ReportGenerator()
    content = gen.generate_daily_report(d)
    return jsonify({"content": content})


@app.route("/api/report/weekly")
def report_weekly():
    year = request.args.get("year", type=int)
    week = request.args.get("week", type=int)
    gen = ReportGenerator()
    content = gen.generate_weekly_report(year, week)
    return jsonify({"content": content})


@app.route("/api/report/monthly")
def report_monthly():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    gen = ReportGenerator()
    content = gen.generate_monthly_report(year, month)
    return jsonify({"content": content})


@app.route("/api/report/quarterly")
def report_quarterly():
    year = request.args.get("year", type=int)
    quarter = request.args.get("quarter", type=int)
    gen = ReportGenerator()
    content = gen.generate_quarterly_report(year, quarter)
    return jsonify({"content": content})


@app.route("/api/report/range")
def report_range():
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    if not start_str or not end_str:
        return jsonify({"error": "缺少必要参数: start 和 end"}), 400
    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except ValueError:
        return jsonify({"error": "日期格式无效，请使用 YYYY-MM-DD 格式"}), 400
    if start > end:
        return jsonify({"error": "开始日期不能晚于结束日期"}), 400
    gen = ReportGenerator()
    content = gen.generate_range_report(start, end)
    return jsonify({"content": content})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)

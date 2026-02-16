/* ========== State ========== */
let currentPage = "daily";
let dailyDate = todayISO();
let weeklyYear, weeklyWeek;
let reportMarkdown = "";
let addTarget = "daily"; // "daily" | "weekly"

const PRIORITIES = ["紧急重要", "紧急不重要", "不紧急重要", "不紧急不重要"];
const STATUS_NAMES = { todo: "待办", in_progress: "进行中", done: "已完成", cancelled: "已取消" };

/* ========== Init ========== */
document.addEventListener("DOMContentLoaded", () => {
    const iso = getISOYearWeek(new Date());
    weeklyYear = iso.year;
    weeklyWeek = iso.week;

    initTheme();
    initNav();
    initDailyControls();
    initWeeklyControls();
    initReportControls();
    initModal();

    loadDaily();
});

/* ========== Theme Switcher ========== */
const THEMES = {
    dark:   '极夜黑',
    light:  '简约白',
    nord:   '北欧蓝',
    sakura: '樱花粉',
};

function initTheme() {
    const saved = localStorage.getItem('taskmanager-theme') || 'dark';
    applyTheme(saved);

    const toggleBtn = document.getElementById('theme-toggle');
    const panel = document.getElementById('theme-panel');

    toggleBtn.addEventListener('click', e => {
        e.stopPropagation();
        panel.classList.toggle('visible');
    });

    document.querySelectorAll('.theme-opt').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const theme = btn.dataset.theme;
            applyTheme(theme);
            localStorage.setItem('taskmanager-theme', theme);
            panel.classList.remove('visible');
        });
    });

    document.addEventListener('click', () => {
        panel.classList.remove('visible');
    });
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-opt').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });
    const labelEl = document.querySelector('.theme-toggle-label');
    if (labelEl) labelEl.textContent = THEMES[theme] || '主题风格';
}

/* ========== Navigation ========== */
function initNav() {
    document.querySelectorAll(".nav-item").forEach(el => {
        el.addEventListener("click", e => {
            e.preventDefault();
            const page = el.dataset.page;
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            el.classList.add("active");
            document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
            document.getElementById("page-" + page).classList.add("active");
            currentPage = page;
            if (page === "daily") loadDaily();
            else if (page === "weekly") loadWeekly();
        });
    });
}

/* ========== Daily ========== */
function initDailyControls() {
    const dateInput = document.getElementById("daily-date");
    dateInput.value = dailyDate;
    dateInput.addEventListener("change", () => { dailyDate = dateInput.value; loadDaily(); });
    document.getElementById("daily-prev").addEventListener("click", () => { shiftDate(-1); });
    document.getElementById("daily-next").addEventListener("click", () => { shiftDate(1); });
    document.getElementById("daily-today").addEventListener("click", () => {
        dailyDate = todayISO(); dateInput.value = dailyDate; loadDaily();
    });
    document.getElementById("daily-add-btn").addEventListener("click", () => openModal("daily"));
}

function shiftDate(days) {
    const parts = dailyDate.split("-");
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    d.setDate(d.getDate() + days);
    dailyDate = formatLocalDate(d);
    document.getElementById("daily-date").value = dailyDate;
    loadDaily();
}

async function loadDaily() {
    const data = await api(`/api/daily?date=${dailyDate}`);
    const allTasks = data.tasks.concat(data.carryover || []);
    renderStats("daily-stats", allTasks);
    renderQuadrants("daily-tasks", data.tasks, data.carryover || [], "daily");
}

/* ========== Weekly ========== */
function initWeeklyControls() {
    updateWeekLabel();
    document.getElementById("weekly-prev").addEventListener("click", () => { shiftWeek(-1); });
    document.getElementById("weekly-next").addEventListener("click", () => { shiftWeek(1); });
    document.getElementById("weekly-current").addEventListener("click", () => {
        const iso = getISOYearWeek(new Date());
        weeklyYear = iso.year; weeklyWeek = iso.week; updateWeekLabel(); loadWeekly();
    });
    document.getElementById("weekly-add-btn").addEventListener("click", () => openModal("weekly"));

    // Goals
    document.getElementById("weekly-goal-add-btn").addEventListener("click", () => {
        document.getElementById("goal-add-form").classList.remove("hidden");
        document.getElementById("goal-input").focus();
    });
    document.getElementById("goal-cancel").addEventListener("click", () => {
        document.getElementById("goal-add-form").classList.add("hidden");
    });
    document.getElementById("goal-submit").addEventListener("click", async () => {
        const input = document.getElementById("goal-input");
        const desc = input.value.trim();
        if (!desc) return;
        await api("/api/weekly/goals", "POST", { description: desc, year: weeklyYear, week: weeklyWeek });
        input.value = "";
        document.getElementById("goal-add-form").classList.add("hidden");
        toast("目标已添加");
        loadWeekly();
    });
    document.getElementById("goal-input").addEventListener("keydown", e => {
        if (e.key === "Enter") { e.preventDefault(); document.getElementById("goal-submit").click(); }
    });
}

function shiftWeek(n) {
    weeklyWeek += n;
    if (weeklyWeek < 1) { weeklyYear--; weeklyWeek = getISOWeeksInYear(weeklyYear); }
    const maxW = getISOWeeksInYear(weeklyYear);
    if (weeklyWeek > maxW) { weeklyYear++; weeklyWeek = 1; }
    updateWeekLabel();
    loadWeekly();
}

function updateWeekLabel() {
    document.getElementById("weekly-label").textContent = `${weeklyYear} 年第 ${weeklyWeek} 周`;
    document.getElementById("report-week-label").textContent = `${weeklyYear} 年第 ${weeklyWeek} 周`;
}

async function loadWeekly() {
    const data = await api(`/api/weekly?year=${weeklyYear}&week=${weeklyWeek}`);
    const allTasks = data.tasks.concat(data.carryover || []);
    renderStats("weekly-stats", allTasks);
    renderGoals(data.goals);
    renderQuadrants("weekly-tasks", data.tasks, data.carryover || [], "weekly");
}

function renderGoals(goals) {
    const wrap = document.getElementById("weekly-goals");
    if (!goals.length) {
        wrap.innerHTML = '<p class="empty-hint">暂无目标, 点击上方添加</p>';
        return;
    }
    wrap.innerHTML = goals.map((g, i) => `
        <div class="goal-item">
            <div class="goal-check ${g.completed ? "completed" : ""}" data-idx="${i}">${g.completed ? "&#10003;" : ""}</div>
            <span class="goal-text ${g.completed ? "completed" : ""}">${esc(g.description)}</span>
            <button class="goal-delete" data-idx="${i}">&times;</button>
        </div>
    `).join("");

    wrap.querySelectorAll(".goal-check").forEach(el => {
        el.addEventListener("click", async () => {
            const idx = parseInt(el.dataset.idx);
            const action = el.classList.contains("completed") ? "undo" : "done";
            await api(`/api/weekly/goals/${idx}`, "PUT", { action, year: weeklyYear, week: weeklyWeek });
            loadWeekly();
        });
    });
    wrap.querySelectorAll(".goal-delete").forEach(el => {
        el.addEventListener("click", async () => {
            if (!confirm("确定删除该目标?")) return;
            await api(`/api/weekly/goals/${el.dataset.idx}?year=${weeklyYear}&week=${weeklyWeek}`, "DELETE");
            toast("目标已删除");
            loadWeekly();
        });
    });
}

/* ========== Report ========== */
function initReportControls() {
    const typeSelect = document.getElementById("report-type");
    const reportDate = document.getElementById("report-date");
    reportDate.value = dailyDate;

    // initialise month picker to current month
    const today = new Date();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    document.getElementById("report-month").value = `${today.getFullYear()}-${mm}`;

    // initialise quarter year selector (current year ± 2)
    const qYearSel = document.getElementById("report-quarter-year");
    const curYear = today.getFullYear();
    for (let y = curYear - 2; y <= curYear + 1; y++) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = `${y}年`;
        if (y === curYear) opt.selected = true;
        qYearSel.appendChild(opt);
    }
    // pre-select current quarter
    const curQ = Math.floor(today.getMonth() / 3) + 1;
    document.getElementById("report-quarter-q").value = curQ;

    // initialise range pickers to current month
    document.getElementById("report-range-start").value =
        `${today.getFullYear()}-${mm}-01`;
    document.getElementById("report-range-end").value = dailyDate;

    const pickers = ["report-date-picker", "report-week-picker",
                     "report-month-picker", "report-quarter-picker",
                     "report-range-picker"];
    const typePickerMap = {
        daily: "report-date-picker",
        weekly: "report-week-picker",
        monthly: "report-month-picker",
        quarterly: "report-quarter-picker",
        range: "report-range-picker",
    };

    typeSelect.addEventListener("change", () => {
        const active = typePickerMap[typeSelect.value];
        pickers.forEach(id =>
            document.getElementById(id).classList.toggle("hidden", id !== active)
        );
    });

    document.getElementById("report-generate").addEventListener("click", generateReport);
    document.getElementById("report-copy").addEventListener("click", () => {
        if (!reportMarkdown) return;
        navigator.clipboard.writeText(reportMarkdown).then(() => toast("已复制到剪贴板"));
    });
}

async function generateReport() {
    const type = document.getElementById("report-type").value;
    let data;
    if (type === "daily") {
        const d = document.getElementById("report-date").value;
        data = await api(`/api/report/daily?date=${d}`);
    } else if (type === "weekly") {
        data = await api(`/api/report/weekly?year=${weeklyYear}&week=${weeklyWeek}`);
    } else if (type === "monthly") {
        const [year, month] = document.getElementById("report-month").value.split("-");
        data = await api(`/api/report/monthly?year=${year}&month=${parseInt(month)}`);
    } else if (type === "quarterly") {
        const year = document.getElementById("report-quarter-year").value;
        const quarter = document.getElementById("report-quarter-q").value;
        data = await api(`/api/report/quarterly?year=${year}&quarter=${quarter}`);
    } else {
        const start = document.getElementById("report-range-start").value;
        const end = document.getElementById("report-range-end").value;
        data = await api(`/api/report/range?start=${start}&end=${end}`);
    }
    reportMarkdown = data.content;
    let html;
    if (typeof marked !== "undefined") {
        const rawHtml = marked.parse(data.content);
        html = typeof DOMPurify !== "undefined" ? DOMPurify.sanitize(rawHtml) : rawHtml;
    } else {
        html = `<pre>${esc(data.content)}</pre>`;
    }
    document.getElementById("report-content").innerHTML = html;
    toast("报告已生成");
}

/* ========== Render Stats ========== */
function renderStats(containerId, tasks) {
    const total = tasks.length;
    const done = tasks.filter(t => t.status === "done").length;
    const ip = tasks.filter(t => t.status === "in_progress").length;
    const todo = tasks.filter(t => t.status === "todo").length;
    const rate = total ? Math.round(done / total * 100) : 0;

    document.getElementById(containerId).innerHTML = `
        <div class="stat-card"><div class="stat-value total">${total}</div><div class="stat-label">总任务</div></div>
        <div class="stat-card"><div class="stat-value done">${done}</div><div class="stat-label">已完成</div></div>
        <div class="stat-card"><div class="stat-value progress">${ip}</div><div class="stat-label">进行中</div></div>
        <div class="stat-card"><div class="stat-value todo">${todo}</div><div class="stat-label">待办</div></div>
        <div class="stat-card"><div class="stat-value rate">${rate}%</div><div class="stat-label">完成率</div></div>
    `;
}

/* ========== Render Quadrants ========== */
function renderQuadrants(gridId, currentTasks, carryoverTasks, type) {
    const grid = document.getElementById(gridId);
    const prefix = type === "daily" ? "daily" : "weekly";
    const qIds = { "紧急重要": "ui", "紧急不重要": "uni", "不紧急重要": "nui", "不紧急不重要": "nuni" };

    for (const priority of PRIORITIES) {
        const body = grid.querySelector(`.quadrant-body[data-priority="${priority}"]`);
        const current = currentTasks.filter(t => t.priority === priority);
        const carryover = carryoverTasks.filter(t => t.priority === priority);
        const total = current.length + carryover.length;

        // Update count
        const countEl = document.getElementById(`${prefix}-q-${qIds[priority]}-count`);
        if (countEl) countEl.textContent = total;

        if (total === 0) {
            body.innerHTML = '<p class="empty-hint">拖拽任务到此处</p>';
        } else {
            let html = "";
            for (const t of current) {
                html += renderTaskCard(t, type);
            }
            for (const t of carryover) {
                html += renderTaskCard(t, type);
            }
            body.innerHTML = html;
        }

        // Bind task actions
        bindTaskActions(body, type);

        // Setup drag-and-drop on body
        setupDropZone(body, type);
    }

    // Setup drag on all cards
    grid.querySelectorAll(".task-card").forEach(card => {
        setupDraggable(card);
    });
}

/* ========== Task Card HTML ========== */
function renderTaskCard(t, type) {
    const pctClass = t.progress >= 100 ? "complete" : "";
    const tags = t.tags.map(tag => `<span class="tag">${esc(tag)}</span>`).join("");
    const statusLabel = STATUS_NAMES[t.status] || t.status;
    const isCarryover = t.carryover === true;
    const carryoverClass = isCarryover ? " carryover" : "";
    const sourceDate = isCarryover ? (t.source || "") : "";

    let meta = "";
    if (t.created_at) meta += `<span>创建: ${t.created_at}</span>`;
    if (t.started_at) meta += `<span>开始: ${t.started_at}</span>`;
    if (t.completed_at) meta += `<span>完成: ${t.completed_at}</span>`;
    if (t.due_date) meta += `<span>截止: ${t.due_date}</span>`;

    let notes = "";
    if (t.notes) notes = `<div class="task-notes"><strong>备注:</strong> ${esc(t.notes)}</div>`;
    if (t.description) notes += `<div class="task-notes"><strong>描述:</strong> ${esc(t.description)}</div>`;

    // Determine the date/week for API calls (use source for carryover tasks)
    const dataDateAttr = isCarryover ? `data-source="${esc(sourceDate)}"` : "";

    // Actions based on status
    let actions = "";
    if (t.status === "todo") {
        actions = `
            <button class="act-start" data-id="${t.id}" data-action="start">开始</button>
            <button class="act-done" data-id="${t.id}" data-action="done">完成</button>
            <button class="act-delete" data-id="${t.id}" data-action="delete">删除</button>
        `;
    } else if (t.status === "in_progress") {
        actions = `
            <button class="act-done" data-id="${t.id}" data-action="done">完成</button>
            <button class="act-cancel" data-id="${t.id}" data-action="cancel">取消</button>
            <button data-id="${t.id}" data-action="toggle-progress">进度</button>
            <button data-id="${t.id}" data-action="toggle-note">备注</button>
            <button class="act-delete" data-id="${t.id}" data-action="delete">删除</button>
        `;
    } else if (t.status === "done") {
        actions = `<button class="act-delete" data-id="${t.id}" data-action="delete">删除</button>`;
    } else {
        actions = `<button class="act-delete" data-id="${t.id}" data-action="delete">删除</button>`;
    }

    return `
    <div class="task-card status-${t.status}${carryoverClass}" data-id="${t.id}" data-priority="${t.priority}" ${dataDateAttr} draggable="true">
        <div class="task-header">
            <span class="task-title">${esc(t.title)}</span>
            <span class="status-badge sb-${t.status}">${statusLabel}</span>
            ${isCarryover ? `<span class="carryover-badge">遗留 ${sourceDate}</span>` : ""}
        </div>
        ${tags ? `<div class="task-tags">${tags}</div>` : ""}
        <div class="task-meta">${meta} <span>ID: ${t.id}</span></div>
        <div class="progress-bar-wrap">
            <div class="progress-bar-fill ${pctClass}" style="width:${t.progress}%"></div>
        </div>
        ${notes}
        <div class="task-actions">${actions}</div>
        <div class="inline-edit hidden" data-edit="progress" data-id="${t.id}">
            <input type="range" min="0" max="100" step="5" value="${t.progress}">
            <span class="val">${t.progress}%</span>
            <button class="btn-sm act-done" data-id="${t.id}" data-action="save-progress">保存</button>
        </div>
        <div class="inline-edit hidden" data-edit="note" data-id="${t.id}">
            <input type="text" placeholder="输入备注..." value="${esc(t.notes || "")}">
            <button class="btn-sm act-done" data-id="${t.id}" data-action="save-note">保存</button>
        </div>
    </div>`;
}

/* ========== Bind Task Actions ========== */
function bindTaskActions(container, type) {
    container.querySelectorAll(".task-actions button").forEach(btn => {
        btn.addEventListener("click", e => {
            e.stopPropagation();
            handleTaskAction(btn.dataset.id, btn.dataset.action, type, container);
        });
    });
    // Range sliders
    container.querySelectorAll('.inline-edit[data-edit="progress"] input[type="range"]').forEach(slider => {
        slider.addEventListener("input", () => {
            slider.nextElementSibling.textContent = slider.value + "%";
        });
    });
    // Save progress
    container.querySelectorAll('[data-action="save-progress"]').forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            const card = container.querySelector(`.task-card[data-id="${id}"]`);
            const slider = container.querySelector(`.inline-edit[data-edit="progress"][data-id="${id}"] input[type="range"]`);
            const body = { action: "progress", value: parseInt(slider.value) };
            applyDateContext(body, type, card);
            await api(`/api/${type}/${id}`, "PUT", body);
            toast("进度已更新");
            type === "daily" ? loadDaily() : loadWeekly();
        });
    });
    // Save note
    container.querySelectorAll('[data-action="save-note"]').forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            const card = container.querySelector(`.task-card[data-id="${id}"]`);
            const input = container.querySelector(`.inline-edit[data-edit="note"][data-id="${id}"] input`);
            const body = { action: "note", value: input.value };
            applyDateContext(body, type, card);
            await api(`/api/${type}/${id}`, "PUT", body);
            toast("备注已更新");
            type === "daily" ? loadDaily() : loadWeekly();
        });
    });
}

function applyDateContext(body, type, card) {
    const source = card ? card.dataset.source : null;
    if (type === "daily") {
        body.date = source || dailyDate;
    } else {
        if (source) {
            // source format: "YYYY-WNN"
            const parts = source.split("-W");
            body.year = parseInt(parts[0]);
            body.week = parseInt(parts[1]);
        } else {
            body.year = weeklyYear;
            body.week = weeklyWeek;
        }
    }
}

async function handleTaskAction(id, action, type, container) {
    const card = container.querySelector(`.task-card[data-id="${id}"]`);
    if (action === "toggle-progress") {
        container.querySelector(`.inline-edit[data-edit="progress"][data-id="${id}"]`).classList.toggle("hidden");
        return;
    }
    if (action === "toggle-note") {
        container.querySelector(`.inline-edit[data-edit="note"][data-id="${id}"]`).classList.toggle("hidden");
        return;
    }
    if (action === "delete") {
        if (!confirm("确定删除该任务?")) return;
        let qs;
        const source = card ? card.dataset.source : null;
        if (type === "daily") {
            qs = `?date=${source || dailyDate}`;
        } else {
            if (source) {
                const parts = source.split("-W");
                qs = `?year=${parts[0]}&week=${parts[1]}`;
            } else {
                qs = `?year=${weeklyYear}&week=${weeklyWeek}`;
            }
        }
        await api(`/api/${type}/${id}${qs}`, "DELETE");
        toast("任务已删除");
    } else {
        const body = { action };
        applyDateContext(body, type, card);
        await api(`/api/${type}/${id}`, "PUT", body);
        toast(action === "start" ? "任务已开始" : action === "done" ? "任务已完成" : "任务已取消");
    }
    type === "daily" ? loadDaily() : loadWeekly();
}

/* ========== Drag and Drop ========== */
let draggedCard = null;

function setupDraggable(card) {
    card.addEventListener("dragstart", e => {
        draggedCard = card;
        card.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", card.dataset.id);
    });
    card.addEventListener("dragend", () => {
        if (draggedCard) draggedCard.classList.remove("dragging");
        draggedCard = null;
        document.querySelectorAll(".quadrant-body.drag-over").forEach(el => el.classList.remove("drag-over"));
        document.querySelectorAll(".drag-placeholder").forEach(el => el.remove());
    });
}

function setupDropZone(body, type) {
    if (body.dataset.dropReady) return;
    body.dataset.dropReady = "1";

    body.addEventListener("dragover", e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        body.classList.add("drag-over");

        // Position placeholder
        const afterCard = getDragAfterElement(body, e.clientY);
        const placeholder = body.querySelector(".drag-placeholder") || createPlaceholder();
        if (!body.contains(placeholder)) body.appendChild(placeholder);
        if (afterCard) {
            body.insertBefore(placeholder, afterCard);
        } else {
            body.appendChild(placeholder);
        }
    });

    body.addEventListener("dragleave", e => {
        if (!body.contains(e.relatedTarget)) {
            body.classList.remove("drag-over");
            const ph = body.querySelector(".drag-placeholder");
            if (ph) ph.remove();
        }
    });

    body.addEventListener("drop", async e => {
        e.preventDefault();
        body.classList.remove("drag-over");
        const ph = body.querySelector(".drag-placeholder");
        if (ph) ph.remove();

        if (!draggedCard) return;
        // Capture local reference before any await, because the dragend event
        // fires during await and sets the global draggedCard to null.
        const card = draggedCard;

        const taskId = card.dataset.id;
        const oldPriority = card.dataset.priority;
        const newPriority = body.dataset.priority;
        const isCarryover = !!card.dataset.source;

        // If priority changed, update via API
        if (oldPriority !== newPriority) {
            const updateBody = { action: "priority", value: newPriority };
            applyDateContext(updateBody, type, card);
            await api(`/api/${type}/${taskId}`, "PUT", updateBody);
        }

        // Reorder: collect all task IDs in the new quadrant order (current tasks only)
        // Move the card visually first
        const afterCard = getDragAfterElement(body, e.clientY);
        if (afterCard) {
            body.insertBefore(card, afterCard);
        } else {
            body.appendChild(card);
        }
        card.dataset.priority = newPriority;

        // Collect order for non-carryover tasks across all quadrants
        if (!isCarryover) {
            const grid = body.closest(".quadrant-grid");
            const allIds = [];
            grid.querySelectorAll(".task-card:not([data-source])").forEach(c => {
                allIds.push(c.dataset.id);
            });
            const reorderBody = { order: allIds };
            if (type === "daily") {
                reorderBody.date = dailyDate;
                await api("/api/daily/reorder", "PUT", reorderBody);
            } else {
                reorderBody.year = weeklyYear;
                reorderBody.week = weeklyWeek;
                await api("/api/weekly/reorder", "PUT", reorderBody);
            }
        }

        toast(oldPriority !== newPriority ? "分类已更新" : "顺序已调整");
        type === "daily" ? loadDaily() : loadWeekly();
    });
}

function createPlaceholder() {
    const ph = document.createElement("div");
    ph.className = "drag-placeholder";
    return ph;
}

function getDragAfterElement(container, y) {
    const cards = [...container.querySelectorAll(".task-card:not(.dragging)")];
    let closest = null;
    let closestOffset = Number.NEGATIVE_INFINITY;
    for (const card of cards) {
        const box = card.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closestOffset) {
            closestOffset = offset;
            closest = card;
        }
    }
    return closest;
}

/* ========== Modal ========== */
function initModal() {
    const overlay = document.getElementById("modal-overlay");
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-cancel-btn").addEventListener("click", closeModal);
    overlay.addEventListener("click", e => { if (e.target === overlay) closeModal(); });

    document.getElementById("task-form").addEventListener("submit", async e => {
        e.preventDefault();
        const title = document.getElementById("form-title").value.trim();
        if (!title) return;

        const payload = {
            title,
            priority: document.getElementById("form-priority").value,
            tags: document.getElementById("form-tags").value,
            description: document.getElementById("form-desc").value,
        };

        if (addTarget === "daily") {
            payload.date = dailyDate;
            await api("/api/daily", "POST", payload);
            toast("每日任务已添加");
            loadDaily();
        } else {
            payload.year = weeklyYear;
            payload.week = weeklyWeek;
            payload.due_date = document.getElementById("form-due").value;
            await api("/api/weekly", "POST", payload);
            toast("每周任务已添加");
            loadWeekly();
        }
        closeModal();
    });
}

function openModal(target) {
    addTarget = target;
    document.getElementById("modal-title").textContent = target === "daily" ? "添加每日任务" : "添加每周任务";
    document.getElementById("form-due-group").classList.toggle("hidden", target === "daily");
    document.getElementById("task-form").reset();
    document.getElementById("modal-overlay").classList.remove("hidden");
    document.getElementById("form-title").focus();
}

function closeModal() {
    document.getElementById("modal-overlay").classList.add("hidden");
}

/* ========== API Helper ========== */
async function api(url, method = "GET", body = null) {
    const opts = { method, headers: {} };
    if (body) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
        let errMsg = `请求失败 (${res.status})`;
        try {
            const errData = await res.json();
            if (errData.error) errMsg = errData.error;
        } catch (_) { /* 忽略JSON解析失败 */ }
        toast(`错误: ${errMsg}`);
        throw new Error(errMsg);
    }
    return res.json();
}

/* ========== Toast ========== */
function toast(msg) {
    const el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.remove("hidden");
    el.classList.add("show");
    setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.classList.add("hidden"), 300); }, 2000);
}

/* ========== Utilities ========== */
function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

function formatLocalDate(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function todayISO() {
    return formatLocalDate(new Date());
}

function getISOYearWeek(d) {
    const date = new Date(d.getTime());
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
    const yearStart = new Date(date.getFullYear(), 0, 4);
    const week = 1 + Math.round(((date - yearStart) / 86400000 - 3 + (yearStart.getDay() + 6) % 7) / 7);
    return { year: date.getFullYear(), week };
}

function getISOWeeksInYear(year) {
    const d = new Date(year, 11, 28);
    return getISOYearWeek(d).week;
}

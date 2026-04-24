from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timezone
import psutil
import urllib.request
import urllib.error
import json as json_module
import os

from app.extensions import db
from app.models import Task, TaskHistory, User, UserModuleAccess, AppEntry, AgentMessage
from datetime import datetime as dt
from app.scheduler import check_daily_notifications, check_daily_summary, check_weekly_briefing, reset_daily_tasks

dashboard_bp = Blueprint('dashboard', __name__)

# --- ROUTES ---


@dashboard_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.dashboard_view'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.complete, Task.due_date).all()
    visible_tasks = []
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    for t in all_tasks:
        if not t.complete:
            visible_tasks.append(t)
        elif t.recurrence != 'none':
            visible_tasks.append(t)
        else:
            if t.last_completed and t.last_completed >= today_start:
                visible_tasks.append(t)

    apps = AppEntry.query.filter_by(is_active=True).order_by(AppEntry.order_index).limit(8).all()
    total_apps = AppEntry.query.filter_by(is_active=True).count()
    return render_template('main/dashboard.html', tasks=visible_tasks, now=datetime.now(),
                           apps=apps, total_apps=total_apps)


@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@dashboard_bp.route('/settings/profile', methods=['POST'])
@login_required
def settings_profile():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    if not username:
        flash('Username cannot be empty.', 'error')
        return redirect(url_for('dashboard.settings'))
    existing = User.query.filter(User.username == username, User.id != current_user.id).first()
    if existing:
        flash('Username already taken.', 'error')
        return redirect(url_for('dashboard.settings'))
    current_user.username = username
    current_user.email = email
    db.session.commit()
    flash('Profile updated.', 'success')
    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/settings/password', methods=['POST'])
@login_required
def settings_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')
    if not check_password_hash(current_user.password, current_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('dashboard.settings'))
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('dashboard.settings'))
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('dashboard.settings'))
    current_user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/settings/gym_day', methods=['POST'])
@login_required
def settings_gym_day():
    day = int(request.form.get('day', 1))
    if 1 <= day <= 7:
        current_user.current_gym_day = day
        db.session.commit()
        flash(f'Gym day set to Day {day}.', 'success')
    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/dev')
@login_required
def dev_panel():
    if current_user.role != 'dev':
        flash("Access Denied: Developer clearance required.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    users = User.query.all()
    modules = ['gym', 'nutrition', 'tasks', 'applications']
    # Build a dict: {user_id: {module: enabled}}
    access_map = {}
    for u in users:
        access_map[u.id] = {}
        for m in modules:
            rec = UserModuleAccess.query.filter_by(user_id=u.id, module=m).first()
            access_map[u.id][m] = rec.enabled if rec else True

    return render_template('main/dev_panel.html', users=users, modules=modules, access_map=access_map)


@dashboard_bp.route('/dev/toggle_module', methods=['POST'])
@login_required
def toggle_module():
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    module = data.get('module')
    enabled = data.get('enabled', True)

    if module not in ('gym', 'nutrition', 'tasks', 'applications'):
        return jsonify({'success': False, 'error': 'Invalid module'}), 400

    rec = UserModuleAccess.query.filter_by(user_id=user_id, module=module).first()
    if rec:
        rec.enabled = enabled
    else:
        rec = UserModuleAccess(user_id=user_id, module=module, enabled=enabled)
        db.session.add(rec)
    db.session.commit()
    return jsonify({'success': True})


# --- APPS ROUTES ---

@dashboard_bp.route('/apps')
@login_required
def all_apps():
    apps = AppEntry.query.order_by(AppEntry.order_index, AppEntry.name).all()
    return render_template('apps/index.html', apps=apps)


@dashboard_bp.route('/apps/add', methods=['POST'])
@login_required
def add_app():
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    name = request.form.get('name', '').strip()
    url = request.form.get('url', '').strip()
    icon = request.form.get('icon', 'fa-globe').strip()
    color = request.form.get('color', '#3A7D52').strip()
    description = request.form.get('description', '').strip()
    order_index = int(request.form.get('order_index', 0))
    if not name or not url:
        flash('Name and URL are required.', 'error')
        return redirect(url_for('dashboard.all_apps'))
    app_entry = AppEntry(name=name, url=url, icon=icon, color=color,
                         description=description, order_index=order_index)
    db.session.add(app_entry)
    db.session.commit()
    flash(f'App "{name}" added.', 'success')
    return redirect(url_for('dashboard.all_apps'))


@dashboard_bp.route('/apps/update/<int:app_id>', methods=['POST'])
@login_required
def update_app(app_id):
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    entry = AppEntry.query.get_or_404(app_id)
    entry.name = request.form.get('name', entry.name).strip()
    entry.url = request.form.get('url', entry.url).strip()
    entry.icon = request.form.get('icon', entry.icon).strip()
    entry.color = request.form.get('color', entry.color).strip()
    entry.description = request.form.get('description', entry.description or '').strip()
    entry.order_index = int(request.form.get('order_index', entry.order_index))
    entry.is_active = request.form.get('is_active', 'true') == 'true'
    db.session.commit()
    return redirect(url_for('dashboard.all_apps'))


@dashboard_bp.route('/apps/delete/<int:app_id>', methods=['POST'])
@login_required
def delete_app(app_id):
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    entry = AppEntry.query.get_or_404(app_id)
    db.session.delete(entry)
    db.session.commit()
    flash(f'App "{entry.name}" deleted.', 'success')
    return redirect(url_for('dashboard.all_apps'))


@dashboard_bp.route('/api/docker_scan')
@login_required
def docker_scan():
    if current_user.role != 'dev':
        return jsonify({'error': 'Access denied'}), 403
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list()
        hints = []
        seen = set()
        for c in containers:
            # Convention: container name IS the subdomain → name.mybrain.world
            name = c.name
            suggested_url = f'https://{name}.mybrain.world'
            ports = c.ports
            exposed_ports = [
                bindings[0]['HostPort']
                for bindings in ports.values()
                if bindings
            ]
            key = name
            if key in seen:
                continue
            seen.add(key)
            hints.append({
                'name': name,
                'suggested_url': suggested_url,
                'ports': exposed_ports,
                'image': c.image.tags[0] if c.image.tags else c.short_id
            })
        return jsonify(hints)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- USER MANAGEMENT (dev only) ---

@dashboard_bp.route('/dev/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    from werkzeug.security import generate_password_hash
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'user').strip()
    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('dashboard.dev_panel'))
    if User.query.filter_by(username=username).first():
        flash(f'User "{username}" already exists.', 'error')
        return redirect(url_for('dashboard.dev_panel'))
    u = User(username=username, password=generate_password_hash(password), role=role)
    db.session.add(u)
    db.session.commit()
    flash(f'User "{username}" created.', 'success')
    return redirect(url_for('dashboard.dev_panel'))


@dashboard_bp.route('/dev/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    from werkzeug.security import generate_password_hash
    u = User.query.get_or_404(user_id)
    new_role = request.form.get('role', u.role).strip()
    new_password = request.form.get('password', '').strip()
    u.role = new_role
    if new_password:
        u.password = generate_password_hash(new_password)
    db.session.commit()
    flash(f'User "{u.username}" updated.', 'success')
    return redirect(url_for('dashboard.dev_panel'))


@dashboard_bp.route('/dev/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'dev':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    if user_id == current_user.id:
        flash("You can't delete yourself.", 'error')
        return redirect(url_for('dashboard.dev_panel'))
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    flash(f'User "{u.username}" deleted.', 'success')
    return redirect(url_for('dashboard.dev_panel'))

# --- API: BASIC STATS (system + counts) ---


@dashboard_bp.route('/api/stats')
@login_required
def get_stats():
    cpu = psutil.cpu_percent(interval=None)

    mem = psutil.virtual_memory()
    ram_used_gb = round(mem.used / (1024 ** 3), 1)
    ram_total_gb = round(mem.total / (1024 ** 3), 1)
    ram_pct = mem.percent

    d = psutil.disk_usage('/')
    disk_used_gb = round(d.used / (1024 ** 3), 1)
    disk_total_gb = round(d.total / (1024 ** 3), 1)
    disk_pct = d.percent

    task_count = Task.query.filter_by(user_id=current_user.id).count()
    history_count = TaskHistory.query.filter_by(user_id=current_user.id).count()
    version = task_count + history_count

    return jsonify({
        'cpu': cpu,
        'ram_pct': ram_pct, 'ram_used': ram_used_gb, 'ram_total': ram_total_gb,
        'disk_pct': disk_pct, 'disk_used': disk_used_gb, 'disk_total': disk_total_gb,
        'data_version': version
    })


# --- DEV PANEL TRIGGERS (kept here as they are dev tools for scheduler) ---


@dashboard_bp.route('/api/trigger/daily', methods=['POST'])
@login_required
def dev_trigger_daily():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Morning alert triggered!'})


@dashboard_bp.route('/api/test/alert', methods=['POST'])
@login_required
def dev_test_alert():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Urgent alert simulation sent!'})


@dashboard_bp.route('/api/trigger/summary', methods=['POST'])
@login_required
def dev_trigger_summary():
    check_daily_summary(current_app)
    return jsonify({'success': True, 'message': 'Night summary triggered!'})


@dashboard_bp.route('/api/trigger/weekly', methods=['POST'])
@login_required
def dev_trigger_weekly():
    check_weekly_briefing(current_app)
    return jsonify({'success': True, 'message': 'Weekly briefing triggered!'})


@dashboard_bp.route('/api/test/seed', methods=['POST'])
@login_required
def dev_seed_data():
    import random
    tasks = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    if not tasks:
        return jsonify({'success': False, 'message': 'No habits found.'})
    today = date.today()
    added_count = 0
    for i in range(30):
        d = today - timedelta(days=i)
        if d > today:
            continue
        for t in tasks:
            if random.random() > 0.5:
                exists = TaskHistory.query.filter_by(
                    task_id=t.id, completed_date=d).first()
                if not exists:
                    h = TaskHistory(task_id=t.id, completed_date=d,
                                    user_id=current_user.id)
                    db.session.add(h)
                    added_count += 1
    db.session.commit()
    return jsonify({'success': True, 'message': f'Seeded {added_count} history entries.'})


@dashboard_bp.route('/api/test/midnight', methods=['POST'])
@login_required
def dev_trigger_midnight():
    reset_daily_tasks(current_app)
    return jsonify({'success': True, 'message': 'Midnight cleanup ran. Daily tasks reset.'})


# ── Agents Page ───────────────────────────────────────────────────────────────

AGENTS = [
    {
        'id': 'main',
        'name': 'Vanitas',
        'emoji': '🐍',
        'role': 'Primary Assistant',
        'model': 'gemini-2.5-flash',
        'telegram': '@vanitas_oc_bot',
        'description': 'Main social interface. Handles daily conversation, delegates complex tasks to Peccata and research to Mundi. Always online.',
        'color': '#22C55E',
        'can_delegate': ['peccata', 'argos', 'mundi'],
        'can_chat': True,
        'agent_api_id': 'main',
    },
    {
        'id': 'peccata',
        'name': 'Peccata',
        'emoji': '💻',
        'role': 'Engineering Sub-Agent',
        'model': 'gemini-2.5-flash',
        'telegram': '@peccata_bot',
        'description': 'Developer and engineer. Writes code, edits files, manages infrastructure. Has full VPS access via SSH from the sandbox.',
        'color': '#60A5FA',
        'can_delegate': [],
        'can_chat': True,
        'agent_api_id': 'peccata',
    },
    {
        'id': 'argos',
        'name': 'Argos',
        'emoji': '📡',
        'role': 'Self-Improvement Loop',
        'model': 'gemini-2.5-pro',
        'telegram': None,
        'description': 'Autonomous agent. Runs daily at 06:00 — reads bot metrics, queries Perplexity, synthesizes strategy, edits the trading bot via Claude Code.',
        'color': '#A78BFA',
        'can_delegate': [],
        'can_chat': False,
        'view_type': 'log',
        'agent_api_id': 'argos',
    },
    {
        'id': 'mundi',
        'name': 'Mundi',
        'emoji': '🌍',
        'role': 'Research Intelligence',
        'model': 'gemini-2.5-flash',
        'telegram': None,
        'description': 'Deep researcher. Uses Gemini CLI (subscription — zero API cost) to generate comprehensive reports. Saves all research as structured markdown artifacts.',
        'color': '#FB923C',
        'can_delegate': [],
        'can_chat': True,
        'agent_api_id': 'mundi',
    },
]


OPENCLAW_HOST  = os.environ.get('OPENCLAW_HOST', '172.17.0.1')
OPENCLAW_PING  = f'http://{OPENCLAW_HOST}:18789'
RUN_WEBHOOK_URL = os.environ.get('RUN_WEBHOOK_URL', 'http://172.17.0.1:9191/run')
WEBHOOK_SECRET  = os.environ.get('DEPLOY_SECRET', '')


@dashboard_bp.route('/agents/chat', methods=['POST'])
@login_required
def agents_chat():
    data = request.get_json()
    message = (data.get('message') or '').strip()
    agent_id = data.get('agent', 'main')          # DB key
    api_agent_id = data.get('api_agent', agent_id)  # OpenClaw agent id

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    # Save user message to DB
    db.session.add(AgentMessage(
        agent_id=agent_id, role='user', source='web',
        content=message, user_id=current_user.id,
    ))
    db.session.commit()

    # Route via deploy-webhook /run so the agent has a real session with full tool execution
    # (completions API is stateless — sessions_spawn and other tools don't fire there)
    payload = json_module.dumps({
        'agent': api_agent_id,
        'message': message,
        'session_suffix': 'web',
    }).encode()

    req = urllib.request.Request(
        RUN_WEBHOOK_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {WEBHOOK_SECRET}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json_module.loads(resp.read())

        reply = result.get('reply', '')
        if not reply:
            return jsonify({'error': result.get('error', 'Empty reply from agent')}), 502

        db.session.add(AgentMessage(
            agent_id=agent_id, role='agent', source='web',
            content=reply, user_id=current_user.id,
        ))
        db.session.commit()
        return jsonify({'reply': reply})

    except urllib.error.HTTPError as e:
        return jsonify({'error': f'Webhook error {e.code}: {e.read().decode()[:200]}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500


SPAWN_WEBHOOK_URL = os.environ.get('SPAWN_WEBHOOK_URL', 'http://172.17.0.1:9191/spawn')
SPAWN_WEBHOOK_SECRET = os.environ.get('DEPLOY_SECRET', '')


@dashboard_bp.route('/agents/spawn', methods=['POST'])
@login_required
def agents_spawn():
    import urllib.request as _req
    data = request.get_json()
    agent_id = data.get('agent', 'mundi')
    task = (data.get('task') or '').strip()
    if not task:
        return jsonify({'error': 'task is required'}), 400
    allowed = {'mundi', 'peccata', 'argos', 'main'}
    if agent_id not in allowed:
        return jsonify({'error': f'agent must be one of {allowed}'}), 400
    try:
        payload = json_module.dumps({'agent': agent_id, 'task': task}).encode()
        req = _req.Request(
            SPAWN_WEBHOOK_URL, data=payload,
            headers={'Authorization': f'Bearer {SPAWN_WEBHOOK_SECRET}', 'Content-Type': 'application/json'},
            method='POST',
        )
        with _req.urlopen(req, timeout=5) as resp:
            result = json_module.loads(resp.read())
        return jsonify({'ok': True, 'status': result.get('status', 'queued')})
    except Exception as e:
        return jsonify({'error': str(e)}), 502


@dashboard_bp.route('/agents/history/<agent_id>')
@login_required
def agents_history(agent_id):
    limit = request.args.get('limit', 100, type=int)
    msgs = (AgentMessage.query
            .filter_by(agent_id=agent_id)
            .order_by(AgentMessage.timestamp.asc())
            .limit(limit)
            .all())
    return jsonify([{
        'role': m.role,
        'source': m.source,
        'content': m.content,
        'timestamp': m.timestamp.isoformat(),
    } for m in msgs])


@dashboard_bp.route('/agents/history/<agent_id>/clear', methods=['POST'])
@login_required
def agents_history_clear(agent_id):
    AgentMessage.query.filter_by(agent_id=agent_id).delete()
    db.session.commit()
    return jsonify({'ok': True})


# ── Agent Activity Logs (Argos + Mundi) ──────────────────────────────────────

ARGOS_DB = {
    'host': os.environ.get('ARGOS_DB_HOST', '172.17.0.1'),
    'port': int(os.environ.get('ARGOS_DB_PORT', 5432)),
    'dbname': 'remastered_core',
    'user': 'admin',
    'password': os.environ.get('ARGOS_DB_PASS', 'remastered_secure_pass'),
}


@dashboard_bp.route('/agents/activity/argos')
@login_required
def argos_activity():
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(**ARGOS_DB, connect_timeout=5)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, report_type, generated_at, content
            FROM argos_reports
            ORDER BY generated_at DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify([{
            'id': r['id'],
            'type': r['report_type'],
            'timestamp': r['generated_at'].isoformat(),
            'content': r['content'],
        } for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/agents/activity/mundi')
@login_required
def mundi_activity():
    msgs = (AgentMessage.query
            .filter_by(agent_id='mundi', role='agent')
            .order_by(AgentMessage.timestamp.desc())
            .limit(20).all())
    return jsonify([{
        'id': m.id,
        'type': 'research',
        'timestamp': m.timestamp.isoformat(),
        'content': m.content,
        'source': m.source,
    } for m in msgs])


# Incoming hook from OpenClaw agents (Telegram messages forwarded by agents)
AGENT_HOOK_SECRET = os.environ.get('AGENT_HOOK_SECRET', 'mybrain-agent-hook-2026')

@dashboard_bp.route('/api/agent-hook', methods=['POST'])
def agent_hook():
    auth = request.headers.get('Authorization', '').replace('Bearer ', '')
    if auth != AGENT_HOOK_SECRET:
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json() or {}
    agent_id = data.get('agent_id', 'main')
    role = data.get('role', 'agent')       # 'user' or 'agent'
    content = (data.get('content') or '').strip()
    source = data.get('source', 'telegram')

    if not content:
        return jsonify({'error': 'empty content'}), 400

    db.session.add(AgentMessage(
        agent_id=agent_id, role=role, source=source, content=content,
    ))
    db.session.commit()
    return jsonify({'ok': True})


@dashboard_bp.route('/agents')
@login_required
def agents_view():
    gateway_online = False
    try:
        urllib.request.urlopen(OPENCLAW_PING, timeout=2)
        gateway_online = True
    except Exception:
        gateway_online = False

    return render_template(
        'main/agents.html',
        agents=AGENTS,
        gateway_online=gateway_online,
    )
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
from datetime import datetime
from typing import Any, Dict
import os

# Load environment from .env if present (for SMTP, tokens, etc.)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Project modules
try:
    from autonomous_manager import AutonomousProjectManager, DatabaseManager, FullyAutonomousManager
except Exception:
    AutonomousProjectManager = None
    DatabaseManager = None
    FullyAutonomousManager = None

try:
    from enhanced_autonomous_pm.interfaces.employee.blueprint import employee_bp
    from enhanced_autonomous_pm.interfaces.manager.blueprint import manager_bp
    from enhanced_autonomous_pm.interfaces.executive.blueprint import executive_bp
    from enhanced_autonomous_pm.interfaces.client.blueprint import client_bp
    from enhanced_autonomous_pm.interfaces.api.blueprint import api_bp
except Exception:
    employee_bp = manager_bp = executive_bp = client_bp = api_bp = None

app = Flask(__name__, template_folder='enhanced_autonomous_pm/web/templates', static_folder='enhanced_autonomous_pm/web/static')
from enhanced_autonomous_pm.core.config import Config
DB_AUTONOMOUS = Config.DATABASE_URL
app.secret_key = os.getenv('SECRET_KEY', 'dev-key')


def _send_email(subject: str, body: str, to_addresses: list[str]) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        host = os.getenv('SMTP_HOST')
        port = int(os.getenv('SMTP_PORT', '587'))
        user = os.getenv('SMTP_USER')
        password = os.getenv('SMTP_PASS')
        from_addr = os.getenv('FROM_EMAIL', user or 'noreply@example.com')
        if not host or not to_addresses:
            return False
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addresses)
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, to_addresses, msg.as_string())
        return True
    except Exception:
        return False


def init_db():
    # Ensure unified 'updates' table exists in autonomous DB
    with sqlite3.connect(DB_AUTONOMOUS) as conn:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE IF NOT EXISTS updates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   project TEXT NOT NULL,
                   update_text TEXT NOT NULL,
                   date TEXT NOT NULL
               )'''
        )
        conn.commit()

def migrate_updates_to_autonomous():
    # Migrate records from legacy project_updates.db into autonomous DB
    legacy = 'project_updates.db'
    if not sqlite3 or not os.path.exists(legacy):
        return
    try:
        with sqlite3.connect(legacy) as src, sqlite3.connect(DB_AUTONOMOUS) as dst:
            sc = src.cursor(); dc = dst.cursor()
            # Map legacy column name `update` to new `update_text`
            sc.execute('SELECT id, name, project, update as update_text, date FROM updates')
            rows = sc.fetchall()
            for _, name, project, update_text, date in rows:
                dc.execute('INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)',
                           (name, project, update_text, date))
            dst.commit()
    except Exception:
        pass


def _is_demo_mode_startup() -> bool:
    if os.getenv('DEMO_MODE', '').lower() in ('1', 'true', 'yes', 'on'):
        return True
    try:
        sentinel = os.path.join('enhanced_autonomous_pm', 'data', 'DEMO_MODE_ON')
        return os.path.exists(sentinel)
    except Exception:
        return False


def ensure_demo_seed():
    """If demo mode is enabled and there are no updates, seed a few.
    Also ensure the autonomous DB is initialized by touching DatabaseManager.
    """
    try:
        # Initialize core DB via DatabaseManager if available
        if DatabaseManager:
            _ = DatabaseManager(DB_AUTONOMOUS)
        os.makedirs(os.path.dirname(DB_AUTONOMOUS) or '.', exist_ok=True)
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS updates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   project TEXT NOT NULL,
                   update_text TEXT NOT NULL,
                   date TEXT NOT NULL
               )''')
            if _is_demo_mode_startup():
                c.execute('SELECT COUNT(*) FROM updates')
                cnt = c.fetchone()[0]
                if cnt == 0:
                    from datetime import datetime
                    now = datetime.utcnow()
                    demo_updates = [
                        ("Sarah Johnson", "PROJ001", "Demo seed: Sprint completed; latency down.", now.strftime('%Y-%m-%d %H:%M:%S')),
                        ("Michael Chen", "PROJ002", "Demo seed: Security review passed; rollout planned.", now.strftime('%Y-%m-%d %H:%M:%S')),
                    ]
                    c.executemany('INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)', demo_updates)
            conn.commit()
    except Exception:
        pass


@app.route('/')
def index():
    return redirect(url_for('manager_bp.manager_home') if manager_bp else '/manager')


@app.errorhandler(Exception)
def handle_api_error(e):
    try:
        path = request.path or ''
        if path.startswith('/api/'):
            return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        pass
    return render_template('error.html', error=str(e)), 500


@app.route('/favicon.ico')
def favicon():
    # Avoid noisy 404s for missing favicon
    return ('', 204)


@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DB_AUTONOMOUS) as conn:
        c = conn.cursor()
        c.execute(
            'SELECT date, project, name, update_text FROM updates ORDER BY date DESC'
        )
        rows = c.fetchall()
    return render_template('dashboards/leadership.html', updates=rows)


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        project = (request.form.get('project') or '').strip()
        update_text = (request.form.get('update') or '').strip()
        if not name or not project or not update_text:
            flash('Please fill in Name, Project, and Update.', 'danger')
            return render_template('forms/update.html', form=request.form)
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)',
                (name, project, update_text, date),
            )
            conn.commit()
        # fire-and-forget email notification if configured
        recipients = [e.strip() for e in os.getenv('LEADERSHIP_EMAILS', '').split(',') if e.strip()]
        if recipients:
            try:
                import threading
                subject = f"Project Update: {project} by {name}"
                body = f"Date: {date}\nProject: {project}\nBy: {name}\n\nUpdate:\n{update_text}"
                threading.Thread(target=_send_email, args=(subject, body, recipients), daemon=True).start()
            except Exception:
                pass
        flash('Update submitted successfully and visible on Leadership Dashboard.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('forms/update.html')


# Register blueprints
if employee_bp:
    app.register_blueprint(employee_bp)
if manager_bp:
    app.register_blueprint(manager_bp)
if executive_bp:
    app.register_blueprint(executive_bp)
if client_bp:
    app.register_blueprint(client_bp)
if api_bp:
    app.register_blueprint(api_bp)


# APIs are provided by the API blueprint under /api


if __name__ == '__main__':
    import os
    init_db()
    migrate_updates_to_autonomous()
    ensure_demo_seed()
    app.run(debug=Config.DEBUG, port=Config.PORT)

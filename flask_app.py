from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
from typing import Any, Dict
import os

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
        name = request.form['name']
        project = request.form['project']
        update_text = request.form['update']
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)',
                (name, project, update_text, date),
            )
            conn.commit()
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
    app.run(debug=Config.DEBUG, port=Config.PORT)

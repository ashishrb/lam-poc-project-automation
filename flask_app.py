from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
from typing import Any, Dict

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
DB_NAME = 'project_updates.db'
DB_AUTONOMOUS = 'autonomous_projects.db'


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE IF NOT EXISTS updates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   project TEXT NOT NULL,
                   update TEXT NOT NULL,
                   date TEXT NOT NULL
               )'''
        )
        conn.commit()


@app.route('/')
def index():
    return redirect(url_for('manager_bp.manager_home') if manager_bp else '/manager')


@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            'SELECT date, project, name, update FROM updates ORDER BY date DESC'
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
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO updates (name, project, update, date) VALUES (?,?,?,?)',
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
    init_db()
    app.run(debug=True)

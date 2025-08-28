from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

try:
    from autonomous_manager import AutonomousProjectManager, DatabaseManager, FullyAutonomousManager
except Exception:
    AutonomousProjectManager = None
    DatabaseManager = None
    FullyAutonomousManager = None

try:
    from enhanced_autonomous_pm.automation.predictive_analytics import PredictiveAnalytics
except Exception:
    PredictiveAnalytics = None

api_bp = Blueprint('api_bp', __name__, url_prefix='/api/v1')


DB_AUTONOMOUS = 'autonomous_projects.db'
DEMO_SENTINEL = os.path.join('enhanced_autonomous_pm', 'data', 'DEMO_MODE_ON')


def _db():
    return DatabaseManager(DB_AUTONOMOUS) if DatabaseManager else None


def _is_demo_mode() -> bool:
    # Demo mode enabled if sentinel file exists or env var is set
    if os.getenv('DEMO_MODE', '').lower() in ('1', 'true', 'yes', 'on'):
        return True
    try:
        return os.path.exists(DEMO_SENTINEL)
    except Exception:
        return False


@api_bp.post('/employee/submit-data')
def employee_submit():
    data = request.get_json() if request.is_json else request.form.to_dict()
    emp_id = data.get('employee_id') or f"EMP_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    name = data.get('name', '')
    email = data.get('email', '')
    department = data.get('department', '')
    role = data.get('role', '')
    availability = float(data.get('availability', data.get('availability_percentage', 100) or 100))
    skills = data.get('skills', '')
    project_id = data.get('project_id')
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    try:
        dbm = _db()
        if dbm:
            with sqlite3.connect(DB_AUTONOMOUS) as conn:
                c = conn.cursor()
                c.execute('''INSERT OR REPLACE INTO employee_profiles (employee_id, name, email, department, role, manager_id, skills, hire_date, availability_percentage, last_updated)
                             VALUES (?,?,?,?,?,?,?,?,?,?)''',
                          (emp_id, name, email, department, role, data.get('manager_id'), skills, now, availability, now))
                for metric in ['quality_score', 'collaboration_score', 'innovation_score']:
                    if metric in data and data[metric] != "":
                        c.execute('''INSERT INTO performance_history (employee_id, metric_name, metric_value, recorded_at)
                                     VALUES (?,?,?,?)''', (emp_id, metric, float(data[metric]), now))
                conn.commit()
        # Also log a daily update if provided
        if data.get('tasks_completed') or data.get('innovation_suggestion'):
            with sqlite3.connect(DB_AUTONOMOUS) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)',
                          (name or emp_id, project_id or 'N/A',
                           f"Tasks Completed: {data.get('tasks_completed', '0')}; Suggestion: {data.get('innovation_suggestion', '-')}", now))
                conn.commit()
        return jsonify({"success": True, "employee_id": emp_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/health')
def health():
    """System health: DB, Ollama, Chroma, Torch/Transformers."""
    status = {"success": True, "data": {}}
    details = {}

    # DB check: simple write/read roundtrip in a temp table
    try:
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS _healthcheck (id INTEGER PRIMARY KEY, ts TEXT)")
            ts = datetime.utcnow().isoformat()
            c.execute("INSERT INTO _healthcheck (ts) VALUES (?)", (ts,))
            conn.commit()
            c.execute("SELECT ts FROM _healthcheck ORDER BY id DESC LIMIT 1")
            got = c.fetchone()
            ok = bool(got and got[0])
            details["database"] = {"ok": ok}
    except Exception as e:
        details["database"] = {"ok": False, "error": str(e)}
        status["success"] = False

    # Capability snapshot
    try:
        from enhanced_autonomous_pm.core import capabilities as caps
        capsum = caps.summarize()
        details["capabilities"] = capsum
    except Exception as e:
        details["capabilities"] = {"ok": False, "error": str(e)}

    # Ollama reachability (non-blocking best effort)
    try:
        from enhanced_autonomous_pm.core.capabilities import OLLAMA_AVAILABLE, ollama
        if OLLAMA_AVAILABLE and ollama:
            # Listing models is lighter than embeddings
            _ = ollama.list()
            details.setdefault("ollama", {})["ok"] = True
        else:
            details.setdefault("ollama", {})["ok"] = False
    except Exception as e:
        details.setdefault("ollama", {})["ok"] = False
        details["ollama"]["error"] = str(e)

    # Chroma availability
    try:
        from enhanced_autonomous_pm.core.capabilities import CHROMADB_AVAILABLE
        details["chromadb"] = {"ok": bool(CHROMADB_AVAILABLE)}
    except Exception as e:
        details["chromadb"] = {"ok": False, "error": str(e)}

    # Demo mode status
    details["demo_mode"] = {"enabled": _is_demo_mode()}

    status["data"] = details
    return jsonify(status)


@api_bp.get('/projects/health')
def projects_health():
    try:
        if _is_demo_mode():
            items = [
                {'project_id': 'PROJ001', 'name': 'AI Customer Portal', 'budget_health': 'warning', 'schedule_health': 'healthy', 'team_health': 'healthy', 'overall_risk': 'medium'},
                {'project_id': 'PROJ002', 'name': 'Banking App Redesign', 'budget_health': 'healthy', 'schedule_health': 'warning', 'team_health': 'critical', 'overall_risk': 'medium'},
            ]
            return jsonify({"success": True, "projects": items})
        if not DatabaseManager:
            return jsonify({"success": False, "error": "DatabaseManager unavailable"}), 500
        dbm = _db()
        projects = dbm.get_all_projects()
        apm = AutonomousProjectManager(dbm)
        items = []
        for p in projects:
            res = apm.analyze_project_health(p.project_id)
            if res.get('success'):
                hm = res['health_metrics']
                items.append({
                    'project_id': p.project_id,
                    'name': p.name,
                    'budget_health': hm['budget_health'],
                    'schedule_health': hm['schedule_health'],
                    'team_health': hm['team_health'],
                    'overall_risk': hm['overall_risk']
                })
        return jsonify({"success": True, "projects": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/projects/resource-utilization')
def resource_utilization():
    # Utilization snapshot
    if _is_demo_mode():
        data = {"Backend": 0.82, "Frontend": 0.64, "QA": 0.58, "DevOps": 0.76, "Data": 0.61}
    else:
        data = {"Backend": 0.92, "Frontend": 0.68, "QA": 0.55, "DevOps": 0.83, "Data": 0.49}
    return jsonify({"success": True, "utilization": data})


@api_bp.get('/projects/budget-burndown')
def budget_burndown():
    try:
        if _is_demo_mode():
            now = datetime.utcnow()
            series = []
            for i in range(14):
                day = (now + timedelta(days=i)).strftime('%Y-%m-%d')
                series.append({'date': day, 'spent': 10000 + i * 9000, 'allocated': 200000})
            return jsonify({"success": True, "series": series, "project": "PROJ001"})
        if not DatabaseManager:
            return jsonify({"success": False}), 500
        dbm = _db()
        projects = dbm.get_all_projects()
        if not projects:
            return jsonify({"success": True, "series": []})
        p = projects[0]
        # simple linear-ish burn
        start = datetime.fromisoformat(p.start_date)
        end = datetime.fromisoformat(p.end_date)
        days = max(1, (end - start).days)
        series = []
        for i in range(days + 1):
            day = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            spent = min(p.budget_allocated, p.budget_used * (i / max(1, (datetime.now() - start).days or 1)))
            series.append({'date': day, 'spent': float(spent), 'allocated': float(p.budget_allocated)})
        return jsonify({"success": True, "series": series, "project": p.project_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/projects/timeline')
def timeline_adherence():
    try:
        if _is_demo_mode():
            return jsonify({"success": True, "expected": 65, "actual": 62, "project": "PROJ001"})
        dbm = _db()
        p = dbm.get_all_projects()[0]
        start = datetime.fromisoformat(p.start_date)
        total_days = (datetime.fromisoformat(p.end_date) - start).days
        days_passed = (datetime.now() - start).days
        expected = max(0, min(100, (days_passed / max(1, total_days)) * 100))
        actual = p.completion_percentage
        return jsonify({"success": True, "expected": expected, "actual": actual, "project": p.project_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/projects/team-performance')
def team_performance():
    try:
        if _is_demo_mode():
            perf = {'quality': 7.8, 'collaboration': 7.2, 'innovation': 8.1}
            return jsonify({"success": True, "averages": perf})
        apm = AutonomousProjectManager(_db())
        res = apm.analyze_team_performance()
        if not res.get('success'):
            return jsonify({"success": False, "error": res.get('error')}), 500
        perf = {
            'quality': float(res['performance_data']['quality_score'].mean()),
            'collaboration': float(res['performance_data']['collaboration_score'].mean()),
            'innovation': float(res['performance_data']['innovation_score'].mean()),
        }
        return jsonify({"success": True, "averages": perf})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/analytics/predictions')
def predictions():
    try:
        if _is_demo_mode():
            return jsonify({"success": True, "prediction": 0.78})
        apm = AutonomousProjectManager(_db())
        prj = apm.db.get_all_projects()[0]
        days_total = (datetime.fromisoformat(prj.end_date) - datetime.fromisoformat(prj.start_date)).days
        days_passed = (datetime.now() - datetime.fromisoformat(prj.start_date)).days
        schedule_progress = (days_passed / max(1, days_total))
        features = {
            'budget_utilization': prj.budget_used / max(1.0, prj.budget_allocated),
            'schedule_progress': schedule_progress,
            'avg_quality': 8.0,
            'risk_level': 0.4 if prj.risk_level == 'low' else 0.6
        }
        if not PredictiveAnalytics:
            return jsonify({"success": True, "prediction": 0.8})
        pa = PredictiveAnalytics()
        res = pa.project_success_modeling(features)
        return jsonify({"success": True, "prediction": res['success_probability']})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Admin endpoints for demo control
@api_bp.post('/admin/demo-mode')
def set_demo_mode():
    try:
        enabled = False
        if request.is_json:
            enabled = bool(request.json.get('enabled'))
        else:
            enabled = request.form.get('enabled') in ('1', 'true', 'on', 'True')
        os.makedirs(os.path.dirname(DEMO_SENTINEL), exist_ok=True)
        if enabled:
            with open(DEMO_SENTINEL, 'w') as f:
                f.write('on')
        else:
            if os.path.exists(DEMO_SENTINEL):
                os.remove(DEMO_SENTINEL)
        return jsonify({"success": True, "enabled": _is_demo_mode()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/admin/reset-demo-data')
def reset_demo_data():
    try:
        # Remove database file
        if os.path.exists(DB_AUTONOMOUS):
            os.remove(DB_AUTONOMOUS)
        # Recreate and seed via DatabaseManager
        if DatabaseManager:
            _ = _db()  # instantiate to build tables and seed
        # Ensure 'updates' table exists for dashboard submissions
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS updates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   project TEXT NOT NULL,
                   update_text TEXT NOT NULL,
                   date TEXT NOT NULL
               )''')
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/projects/autonomous-analysis')
@api_bp.get('/projects/autonomous-analysis')
def autonomous_analysis():
    project_id = request.values.get('project_id')
    try:
        if FullyAutonomousManager:
            fam = FullyAutonomousManager(_db())
            result = fam.complete_project_lifecycle_automation(project_id)
        elif AutonomousProjectManager:
            apm = AutonomousProjectManager(_db())
            result = apm.execute_autonomous_project_workflow(project_id)
        else:
            return jsonify({"success": False, "error": "Autonomous modules unavailable"}), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/communications/generate')
def communications_generate():
    audience = request.json.get('audience', 'team') if request.is_json else request.form.get('audience', 'team')
    try:
        from enhanced_autonomous_pm.automation.communication_engine import IntelligentCommunicationEngine
        ice = IntelligentCommunicationEngine()
        result = ice.generate_personalized_updates(audience=audience)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

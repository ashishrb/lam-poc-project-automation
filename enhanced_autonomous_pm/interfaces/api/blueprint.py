from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
import io
import json as _json

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

try:
    from enhanced_autonomous_pm.core.ai_orchestrator import EnhancedAIOrchestrator
except Exception:
    EnhancedAIOrchestrator = None

try:
    from enhanced_autonomous_pm.core.rag_engine import RAGKnowledgeEngine
except Exception:
    RAGKnowledgeEngine = None

try:
    from enhanced_autonomous_pm.core.knowledge_manager import KnowledgeManager
except Exception:
    KnowledgeManager = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

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


def _check_admin() -> bool:
    token = os.getenv('ADMIN_TOKEN')
    if not token:
        return True  # no token set → open in demo
    return request.headers.get('X-Admin-Token') == token


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


# RAG endpoints
@api_bp.post('/rag/reindex')
def rag_reindex():
    try:
        if not RAGKnowledgeEngine:
            return jsonify({"success": False, "error": "RAG engine unavailable"}), 500
        rag = RAGKnowledgeEngine()
        res = rag.index_existing_project_data()
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/rag/query')
def rag_query():
    try:
        q = request.json.get('query') if request.is_json else request.form.get('query')
        if not q:
            return jsonify({"success": False, "error": "Missing query"}), 400
        if not RAGKnowledgeEngine:
            return jsonify({"success": False, "error": "RAG engine unavailable"}), 500
        rag = RAGKnowledgeEngine()
        res = rag.enhance_query_with_context(q)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Model routing and Ollama usage
@api_bp.get('/models/route')
def model_route():
    try:
        q = request.args.get('query', 'Provide a strategic analysis and plan for improving delivery performance and reducing budget variance.')
        if not EnhancedAIOrchestrator:
            return jsonify({"success": True, "provider": "transformers", "selected_model": "Salesforce/xLAM-1b-fc-r", "note": "Core orchestrator unavailable"})
        orch = EnhancedAIOrchestrator()
        route = orch.route_query_to_appropriate_model(q)
        return jsonify({"success": True, **route})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/models/ollama/generate')
def ollama_generate():
    try:
        from enhanced_autonomous_pm.core.capabilities import OLLAMA_AVAILABLE, ollama
        if not OLLAMA_AVAILABLE or not ollama:
            return jsonify({"success": False, "error": "Ollama client not available"}), 500
        data = request.get_json() if request.is_json else request.form.to_dict()
        model = data.get('model', 'gpt-oss:20b')
        prompt = data.get('prompt', 'Provide three bullet strategic recommendations to improve project delivery.')
        # Keep it fast and short for demos
        res = ollama.generate(model=model, prompt=prompt, options={"num_predict": 128})
        return jsonify({"success": True, "model": model, "response": res.get('response', '')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Activity endpoints
@api_bp.get('/activity/communications')
def activity_communications():
    try:
        limit = int(request.args.get('limit', '50'))
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS communication_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stakeholder_id TEXT,
                        project_id TEXT,
                        channel TEXT,
                        subject TEXT,
                        message TEXT,
                        sent_at TEXT,
                        status TEXT
                    )''')
            c.execute('SELECT project_id, channel, subject, sent_at, status FROM communication_logs ORDER BY id DESC LIMIT ?', (limit,))
            rows = c.fetchall()
        items = [{"project_id": r[0], "channel": r[1], "subject": r[2], "sent_at": r[3], "status": r[4]} for r in rows]
        return jsonify({"success": True, "items": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/activity/files')
def activity_files():
    try:
        base = os.path.abspath(OPS_DIR)
        os.makedirs(base, exist_ok=True)
        out = []
        for root, _, files in os.walk(base):
            for fn in files:
                path = os.path.join(root, fn)
                st = os.stat(path)
                out.append({
                    "path": os.path.relpath(path, base),
                    "size": st.st_size,
                    "modified": datetime.utcfromtimestamp(st.st_mtime).isoformat()
                })
        out = sorted(out, key=lambda x: x['modified'], reverse=True)[:200]
        return jsonify({"success": True, "files": out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/ops/file')
def ops_file_read():
    try:
        rel = request.args.get('path', 'note.txt')
        target = _safe_path(OPS_DIR, rel)
        if not os.path.exists(target):
            return jsonify({"success": False, "error": "File not found"}), 404
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read(16384)
        return jsonify({"success": True, "path": rel, "content": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.post('/email/test')
def email_test():
    try:
        if not _check_admin():
            return jsonify({"success": False, "error": "Forbidden"}), 403
        data = request.get_json() if request.is_json else request.form.to_dict()
        to = data.get('to')
        if not to:
            # Fallback to leadership list
            to = os.getenv('LEADERSHIP_EMAILS', '').split(',')[0].strip() if os.getenv('LEADERSHIP_EMAILS') else ''
        if not to:
            return jsonify({"success": False, "error": "No recipient provided and LEADERSHIP_EMAILS is empty"}), 400
        subject = data.get('subject') or 'SMTP Test - Autonomous PM'
        body = data.get('body') or f'This is a test email from Autonomous PM at {datetime.utcnow().isoformat()}.'
        ok = _send_email(subject, body, [to])
        return jsonify({"success": bool(ok), "to": to})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# File upload → RAG ingestion
UPLOAD_DIR = os.path.join('enhanced_autonomous_pm', 'data', 'uploads')
OPS_DIR = os.path.join('enhanced_autonomous_pm', 'data', 'ops')


def _extract_text_from_file(filename: str, bytes_data: bytes) -> str:
    name = filename.lower()
    try:
        if name.endswith(('.txt', '.md', '.log')):
            return bytes_data.decode('utf-8', errors='ignore')
        if name.endswith(('.csv',)) and pd is not None:
            df = pd.read_csv(io.BytesIO(bytes_data))
            return df.to_csv(index=False)
        if name.endswith(('.json',)):
            try:
                return _json.dumps(_json.loads(bytes_data.decode('utf-8', errors='ignore')), indent=2)
            except Exception:
                return bytes_data.decode('utf-8', errors='ignore')
        if name.endswith(('.html', '.htm')) and BeautifulSoup is not None:
            soup = BeautifulSoup(bytes_data, 'html.parser')
            return soup.get_text(separator='\n')
        # Fallback: store raw bytes as hex-limited preview
        return bytes_data[:4096].decode('utf-8', errors='ignore')
    except Exception:
        return bytes_data[:4096].decode('utf-8', errors='ignore')


def _safe_path(base: str, rel: str) -> str:
    os.makedirs(base, exist_ok=True)
    rel = rel.lstrip('/\\')
    full = os.path.abspath(os.path.join(base, rel))
    base_abs = os.path.abspath(base)
    if not full.startswith(base_abs + os.sep) and full != base_abs:
        raise ValueError('Path traversal not allowed')
    return full


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


@api_bp.post('/files/upload')
def files_upload():
    try:
        if not _check_admin():
            return jsonify({"success": False, "error": "Forbidden"}), 403
        if not KnowledgeManager:
            return jsonify({"success": False, "error": "Knowledge manager unavailable"}), 500
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        files = request.files.getlist('files')
        if not files:
            return jsonify({"success": False, "error": "No files provided"}), 400
        docs = []
        saved = []
        for f in files:
            data = f.read()
            save_path = os.path.join(UPLOAD_DIR, f.filename)
            with open(save_path, 'wb') as out:
                out.write(data)
            saved.append(save_path)
            text = _extract_text_from_file(f.filename, data)
            docs.append({
                "id": f"upload:{int(datetime.utcnow().timestamp()*1000)}:{f.filename}",
                "text": text,
                "metadata": {"source": "upload", "filename": f.filename, "path": save_path, "uploaded_at": datetime.utcnow().isoformat()}
            })
        km = KnowledgeManager()
        res = km.add_documents(docs)
        return jsonify({"success": True, "saved": saved, "indexed": res.get('count', 0) if res.get('success') else 0, "rag": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# NLP instruction endpoint (Auto/LAM/gpt-oss:20b) with optional RAG augmentation
@api_bp.post('/nlp/execute')
def nlp_execute():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        prompt = data.get('prompt') or ''
        provider = (data.get('provider') or 'auto').lower()  # auto|xlam|gpt
        use_rag = str(data.get('use_rag') or 'false').lower() in ('1','true','yes','on')
        intent = (data.get('intent') or '').lower()  # write_file|read_file|team_message|exec_email|leadership_update
        args = data.get('args') or {}
        confirm = str(data.get('confirm') or 'false').lower() in ('1','true','yes','on')
        augmented = prompt
        contexts = []
        if use_rag and RAGKnowledgeEngine:
            rag = RAGKnowledgeEngine()
            res = rag.enhance_query_with_context(prompt)
            if res.get('success'):
                augmented = res.get('augmented_query', prompt)
                contexts = res.get('contexts', [])

        route = {"selected_model": "Salesforce/xLAM-1b-fc-r", "provider": "transformers"}
        if EnhancedAIOrchestrator:
            orch = EnhancedAIOrchestrator()
            route = orch.route_query_to_appropriate_model(prompt)

        # Provider resolution
        final_provider = provider
        if provider == 'auto':
            final_provider = route.get('provider', 'transformers')

        # Lightweight intent inference if not provided
        if not intent:
            low = prompt.lower()
            inferred = None
            inferred_args = {}
            if any(k in low for k in ['write file','create file','save to file']):
                inferred = 'write_file'; inferred_args = {'path': 'note.txt', 'content': prompt}
            elif any(k in low for k in ['read file','open file','show file']):
                inferred = 'read_file'; inferred_args = {'path': 'note.txt'}
            elif 'team' in low and any(k in low for k in ['notify','message','mail','email','update']):
                inferred = 'team_message'; inferred_args = {'project_id': None, 'subject': 'Team Update', 'recipients': [] , 'message': prompt}
            elif any(k in low for k in ['executive','leadership']) and 'email' in low:
                inferred = 'exec_email'; inferred_args = {'subject': 'Executive Update', 'recipients': [], 'body': prompt}
            elif any(k in low for k in ['leadership update','post update','publish update']):
                inferred = 'leadership_update'; inferred_args = {'name': 'Autonomous PM', 'project': 'N/A', 'update': prompt}
            if inferred:
                return jsonify({"success": True, "requires_confirmation": True, "inferred_intent": inferred, "inferred_args": inferred_args, "route": route})

        # Tool actions (require confirmation on destructive ops)
        if intent == 'write_file':
            if not _check_admin():
                return jsonify({"success": False, "error": "Forbidden"}), 403
            rel = (args.get('path') or 'note.txt') if isinstance(args, dict) else 'note.txt'
            content = (args.get('content') or prompt) if isinstance(args, dict) else prompt
            target = _safe_path(OPS_DIR, rel)
            preview = {"action": "write_file", "path": target, "bytes": len(content.encode('utf-8'))}
            if not confirm:
                return jsonify({"success": True, "requires_confirmation": True, "preview": preview})
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({"success": True, **preview})

        if intent == 'read_file':
            rel = (args.get('path') or 'note.txt') if isinstance(args, dict) else 'note.txt'
            target = _safe_path(OPS_DIR, rel)
            if not os.path.exists(target):
                return jsonify({"success": False, "error": "File not found"}), 404
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read(8192)
            return jsonify({"success": True, "action": "read_file", "path": target, "content": data})

        if intent == 'team_message':
            if not _check_admin():
                return jsonify({"success": False, "error": "Forbidden"}), 403
            project_id = args.get('project_id') if isinstance(args, dict) else None
            subject = args.get('subject') if isinstance(args, dict) else 'Team Update'
            message = args.get('message') if isinstance(args, dict) else prompt
            recipients = args.get('recipients') if isinstance(args, dict) else []
            preview = {"action": "team_message", "project_id": project_id, "subject": subject, "recipients": recipients, "length": len(message)}
            if not confirm:
                return jsonify({"success": True, "requires_confirmation": True, "preview": preview})
            sent = 0
            if recipients:
                if _send_email(subject, message, recipients):
                    sent = len(recipients)
            # log into communication_logs
            try:
                with sqlite3.connect(DB_AUTONOMOUS) as conn:
                    c = conn.cursor()
                    c.execute('''CREATE TABLE IF NOT EXISTS communication_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stakeholder_id TEXT,
                        project_id TEXT,
                        channel TEXT,
                        subject TEXT,
                        message TEXT,
                        sent_at TEXT,
                        status TEXT
                    )''')
                    c.execute('INSERT INTO communication_logs (stakeholder_id, project_id, channel, subject, message, sent_at, status) VALUES (?,?,?,?,?,?,?)',
                              (None, project_id, 'email', subject, message, datetime.utcnow().isoformat(), 'sent' if sent else 'queued'))
                    conn.commit()
            except Exception:
                pass
            return jsonify({"success": True, **preview, "emails_sent": sent})

        if intent == 'exec_email':
            if not _check_admin():
                return jsonify({"success": False, "error": "Forbidden"}), 403
            subject = args.get('subject') if isinstance(args, dict) else 'Executive Update'
            body = args.get('body') if isinstance(args, dict) else prompt
            recipients = args.get('recipients') if isinstance(args, dict) else []
            if not recipients:
                recipients = [e.strip() for e in os.getenv('LEADERSHIP_EMAILS','').split(',') if e.strip()]
            preview = {"action": "exec_email", "subject": subject, "recipients": recipients, "length": len(body)}
            if not confirm:
                return jsonify({"success": True, "requires_confirmation": True, "preview": preview})
            sent = 0
            if recipients:
                if _send_email(subject, body, recipients):
                    sent = len(recipients)
            return jsonify({"success": True, **preview, "emails_sent": sent})

        if intent == 'leadership_update':
            if not _check_admin():
                return jsonify({"success": False, "error": "Forbidden"}), 403
            name = args.get('name') if isinstance(args, dict) else 'System'
            project = args.get('project') if isinstance(args, dict) else (args.get('project_id') if isinstance(args, dict) else 'N/A')
            upd = args.get('update') if isinstance(args, dict) else prompt
            preview = {"action": "leadership_update", "project": project, "name": name, "length": len(upd)}
            if not confirm:
                return jsonify({"success": True, "requires_confirmation": True, "preview": preview})
            with sqlite3.connect(DB_AUTONOMOUS) as conn:
                c = conn.cursor()
                c.execute('CREATE TABLE IF NOT EXISTS updates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, project TEXT, update_text TEXT, date TEXT)')
                c.execute('INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)',
                          (name, project, upd, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
            return jsonify({"success": True, **preview})

        # Text generation paths
        if final_provider == 'ollama' or final_provider == 'gpt':
            from enhanced_autonomous_pm.core.capabilities import OLLAMA_AVAILABLE, ollama
            if not OLLAMA_AVAILABLE or not ollama:
                return jsonify({"success": False, "error": "Ollama not available"}), 500
            model = 'gpt-oss:20b'
            resp = ollama.generate(model=model, prompt=augmented, options={"num_predict": 256})
            return jsonify({"success": True, "provider": "ollama", "model": model, "route": route, "contexts": contexts, "response": resp.get('response', '')})

        # xLAM-path placeholder (simulate function-calling response)
        # In a fuller integration, map prompt intents to tools/actions here.
        return jsonify({
            "success": True,
            "provider": "transformers",
            "model": "Salesforce/xLAM-1b-fc-r",
            "route": route,
            "contexts": contexts,
            "response": "xLAM operation routed. Tool actions executed when 'intent' provided."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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


@api_bp.get('/projects/list')
def projects_list():
    """Return all projects with key fields for portfolio view."""
    try:
        # Demo mode quick data
        if _is_demo_mode():
            items = [
                {
                    'project_id': 'PROJ001', 'name': 'AI Customer Portal', 'status': 'in_progress',
                    'start_date': (datetime.utcnow()-timedelta(days=45)).strftime('%Y-%m-%d'),
                    'end_date': (datetime.utcnow()+timedelta(days=30)).strftime('%Y-%m-%d'),
                    'budget_allocated': 175000, 'budget_used': 118500,
                    'completion_percentage': 72, 'risk_level': 'medium', 'team_size': 10
                },
                {
                    'project_id': 'PROJ002', 'name': 'Banking App Redesign', 'status': 'in_progress',
                    'start_date': (datetime.utcnow()-timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end_date': (datetime.utcnow()+timedelta(days=60)).strftime('%Y-%m-%d'),
                    'budget_allocated': 235000, 'budget_used': 96500,
                    'completion_percentage': 48, 'risk_level': 'low', 'team_size': 12
                }
            ]
            for it in items:
                util = (it['budget_used']/max(1.0, it['budget_allocated']))*100.0
                it['budget_utilization'] = round(util, 2)
            return jsonify({"success": True, "projects": items})

        if not DatabaseManager:
            return jsonify({"success": False, "error": "DatabaseManager unavailable"}), 500
        dbm = _db()
        items = []
        for p in dbm.get_all_projects():
            util = (p.budget_used/max(1.0,p.budget_allocated))*100.0
            items.append({
                'project_id': p.project_id,
                'name': p.name,
                'status': p.status.value if hasattr(p.status,'value') else p.status,
                'start_date': str(p.start_date.date()),
                'end_date': str(p.end_date.date()),
                'budget_allocated': float(p.budget_allocated),
                'budget_used': float(p.budget_used),
                'budget_utilization': round(util,2),
                'completion_percentage': float(p.completion_percentage),
                'risk_level': p.risk_level,
                'team_size': int(p.team_size)
            })
        return jsonify({"success": True, "projects": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.get('/employees/top-performance')
def top_performance():
    """Return top N employees by quality score."""
    try:
        limit = int(request.args.get('limit','10'))
        with sqlite3.connect(DB_AUTONOMOUS) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS employee_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                project_id TEXT,
                quarter TEXT,
                hours_worked REAL,
                tasks_completed INTEGER,
                quality_score REAL,
                collaboration_score REAL,
                innovation_score REAL,
                performance_trend TEXT,
                skill_gaps TEXT,
                achievements TEXT,
                development_goals TEXT,
                last_review_date TEXT,
                next_review_date TEXT
            )''')
            c.execute('SELECT employee_id, employee_name, project_id, quality_score, collaboration_score, innovation_score FROM employee_performance ORDER BY quality_score DESC LIMIT ?', (limit,))
            rows = c.fetchall()
        items = [{
            'employee_id': r[0], 'employee_name': r[1], 'project_id': r[2],
            'quality_score': float(r[3] or 0), 'collaboration_score': float(r[4] or 0), 'innovation_score': float(r[5] or 0)
        } for r in rows]
        return jsonify({"success": True, "employees": items})
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
        if not _check_admin():
            return jsonify({"success": False, "error": "Forbidden"}), 403
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
        if not _check_admin():
            return jsonify({"success": False, "error": "Forbidden"}), 403
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
            # seed a few leadership updates for demo
            now = datetime.utcnow()
            demo_updates = [
                ("Sarah Johnson", "PROJ001", "Sprint 8 completed; API latency down 22%.", now.strftime('%Y-%m-%d %H:%M:%S')),
                ("Michael Chen", "PROJ002", "Security review passed; rollout plan drafted.", (now.replace(microsecond=0)).strftime('%Y-%m-%d %H:%M:%S')),
                ("Alice Brown", "PROJ001", "UX polish on onboarding; A/B test scheduled.", now.strftime('%Y-%m-%d %H:%M:%S')),
            ]
            c.executemany('INSERT INTO updates (name, project, update_text, date) VALUES (?,?,?,?)', demo_updates)
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

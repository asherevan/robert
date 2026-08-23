"""Authenticated local web dashboard for the Robert control hub."""

import hmac
import os
import secrets
import string
from functools import wraps

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for

from ServiceManager import get_service_manager

def generate_secret():
    alphabet = string.ascii_letters + string.digits
    secret = ''.join(secrets.choice(alphabet) for _ in range(64))
    return secret

def create_dashboard(service_manager=None):
    """Create the authenticated dashboard application."""
    username = os.environ.get("ROBERT_ADMIN_USERNAME")
    password = os.environ.get("ROBERT_ADMIN_PASSWORD")
    secret_key = os.environ.get("ROBERT_DASHBOARD_SECRET", generate_secret())

    if not username or not password:
        raise RuntimeError(
            "Set ROBERT_ADMIN_USERNAME and ROBERT_ADMIN_PASSWORD before starting "
            "the web dashboard."
        )

    app = Flask(__name__)
    app.secret_key = secret_key or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ROBERT_DASHBOARD_HTTPS") == "1",
    )
    manager = service_manager or get_service_manager()

    def authenticated(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("authenticated"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def csrf_valid():
        token = session.get("csrf_token")
        supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        return bool(token and supplied and hmac.compare_digest(token, supplied))

    @app.before_request
    def add_csrf_token():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))

    @app.get("/login")
    def login():
        if session.get("authenticated"):
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_TEMPLATE, error=None)

    @app.post("/login")
    def login_post():
        submitted_username = request.form.get("username", "")
        submitted_password = request.form.get("password", "")
        valid = hmac.compare_digest(submitted_username, username) and hmac.compare_digest(
            submitted_password, password
        )
        if not valid:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid sign-in details."), 401

        session.clear()
        session["authenticated"] = True
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(request.args.get("next") or url_for("dashboard"))

    @app.post("/logout")
    @authenticated
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @authenticated
    def dashboard():
        return render_template_string(DASHBOARD_TEMPLATE)

    @app.get("/api/status")
    @authenticated
    def api_status():
        status = manager.get_all_status()
        status["debug_output"] = manager.is_debug_output_enabled()
        status["monitoring"] = manager.monitoring
        return jsonify(status)

    @app.get("/api/logs/<service_name>")
    @authenticated
    def api_logs(service_name):
        lines = min(max(request.args.get("lines", default=50, type=int), 1), 200)
        return jsonify({"service": service_name, "lines": manager.get_recent_log_lines(service_name, lines)})

    @app.get("/api/tools")
    @authenticated
    def api_tools():
        success, tools = manager.list_tools()
        return jsonify({"tools": tools, "available": success})

    @app.post("/api/action")
    @authenticated
    def api_action():
        if not csrf_valid():
            return jsonify({"error": "Invalid CSRF token."}), 403

        payload = request.get_json(silent=True) or {}
        action = payload.get("action")
        service = payload.get("service")

        if action == "source_start":
            success = manager.start_sources(service or 'all')
        elif action == "source_stop":
            success = manager.stop_sources(service or 'all')
        elif action == "source_restart":
            success = manager.restart_source(service)
        elif action == "source_pause":
            success = manager.pause_source(service)
        elif action == "source_resume":
            success = manager.resume_source(service)
        elif action == "event":
            success, result = manager.send_event(payload.get("event", {}))
        elif action == "tool":
            success, result = manager.run_tool(payload.get("name", ""), payload.get("args", {}))
        elif action == "start":
            if service == "all":
                manager.start_all()
                success = True
            else:
                success = manager.start_service(service)
        elif action == "stop":
            if service == "all":
                manager.stop_all()
                success = True
            else:
                success = manager.stop_service(service)
        elif action == "restart":
            if service == "all":
                manager.restart_all()
                success = True
            else:
                success = manager.restart_service(service)
        elif action == "debug":
            if payload.get("enabled") is None:
                return jsonify({"error": "Missing debug state."}), 400
            success = manager.set_debug_output(bool(payload["enabled"]))
        elif action == "monitor":
            if payload.get("enabled"):
                manager.start_monitoring()
            else:
                manager.stop_monitoring()
            success = True
        else:
            return jsonify({"error": "Unknown action."}), 400

        status = manager.get_all_status()
        status["debug_output"] = manager.is_debug_output_enabled()
        status["monitoring"] = manager.monitoring
        result_data = {"ok": bool(success), "status": status}
        if action in ("event", "tool"):
            result_data["result"] = result
        return jsonify(result_data)

    @app.get("/api/session")
    @authenticated
    def api_session():
        return jsonify({"csrf_token": session["csrf_token"]})

    return app


LOGIN_TEMPLATE = """
<!doctype html>
<title>Robert Sign In</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui,sans-serif;background:#101820;color:#e8f0f2;display:grid;place-items:center;min-height:100vh;margin:0}
form{background:#1b2b34;padding:2rem;border-radius:12px;width:min(360px,calc(100% - 3rem));box-shadow:0 12px 40px #0006}
h1{margin-top:0}label{display:block;margin:1rem 0 .35rem}input{box-sizing:border-box;width:100%;padding:.75rem;border:1px solid #49616b;border-radius:6px;background:#102027;color:#fff}button{margin-top:1.25rem;width:100%;padding:.75rem;border:0;border-radius:6px;background:#61c0bf;color:#102027;font-weight:700;cursor:pointer}.error{color:#ff9d8d}
</style>
<form method="post"><h1>Robert</h1><p>Sign in to the control dashboard.</p>{% if error %}<p class="error">{{ error }}</p>{% endif %}<label for="username">Username</label><input id="username" name="username" autocomplete="username" required><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required><button type="submit">Sign in</button></form>
"""


DASHBOARD_TEMPLATE = """
<!doctype html>
<title>Robert Control Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{font-family:system-ui,sans-serif;color:#e8f0f2;background:#101820}body{max-width:1100px;margin:0 auto;padding:1.5rem}header{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}.muted{color:#9fb2b8}.toolbar{display:flex;gap:.5rem;flex-wrap:wrap}button{padding:.55rem .8rem;border:1px solid #49616b;border-radius:6px;background:#1b2b34;color:#e8f0f2;cursor:pointer}button:hover{background:#29434d}.danger{border-color:#e48d7c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem;margin:1.5rem 0}.card{border:1px solid #304a54;border-radius:8px;padding:1rem;background:#17252c}.healthy{color:#75d6a0}.bad{color:#ff9d8d}.card h2{font-size:1.05rem;margin:0 0 .6rem}.actions{display:flex;gap:.4rem;flex-wrap:wrap}.logs{background:#0b1216;border:1px solid #304a54;border-radius:8px;padding:1rem;min-height:180px;white-space:pre-wrap;overflow:auto;font:12px ui-monospace,monospace}.logout{margin:0} @media(max-width:600px){body{padding:1rem}}
</style>
<header><div><h1>Robert Control Dashboard</h1><div id="summary" class="muted">Loading status...</div></div><form class="logout" method="post" action="/logout"><button class="danger">Sign out</button></form></header>
<div class="toolbar"><button onclick="allAction('start')">Start services</button><button onclick="allAction('stop')">Stop services</button><button onclick="allAction('restart')">Restart services</button><button onclick="sourceAction('source_start','all')">Start sources</button><button onclick="sourceAction('source_stop','all')">Stop sources</button><button onclick="sourceAction('source_pause','all')">Pause sources</button><button onclick="sourceAction('source_resume','all')">Resume sources</button><button onclick="toggleMonitor()" id="monitor">Start monitoring</button><button onclick="toggleDebug()" id="debug">Debug: on</button><button onclick="sendEvent()">Send event</button><button onclick="runTool()">Run tool</button></div>
<section id="services" class="grid"></section><h2>Recent logs</h2><select id="serviceSelect" onchange="loadLogs()"></select><pre id="logs" class="logs">Select a service.</pre>
<script>
let token, state;
async function request(url, options={}){const response=await fetch(url, options);const contentType=response.headers.get('content-type')||'';const data=contentType.includes('application/json')?await response.json():{};if(!response.ok)throw Error(data.error||`Request failed (${response.status})`);return data}
async function init(){({csrf_token:token}=await request('/api/session'));await refresh();setInterval(()=>refresh().catch(showError),5000)}
async function refresh(){state=await request('/api/status');document.querySelector('#summary').textContent=`${Object.keys(state.services).length} services | monitoring ${state.monitoring?'on':'off'}`;document.querySelector('#debug').textContent=`Debug: ${state.debug_output?'on':'off'}`;document.querySelector('#monitor').textContent=state.monitoring?'Stop monitoring':'Start monitoring';const services=document.querySelector('#services');services.innerHTML='';const select=document.querySelector('#serviceSelect');const selected=select.value;select.innerHTML='';Object.entries(state.services).forEach(([name,s])=>{const sourceActions=s.source?`<button onclick="sourceAction('${s.paused?'source_resume':'source_pause'}','${name}')">${s.paused?'Resume':'Pause'}</button>`:'';services.innerHTML+=`<article class="card"><h2>${name}</h2><div class="${s.health_status==='healthy'?'healthy':'bad'}">${s.paused?'Paused':s.is_running?'Running':'Stopped'} / ${s.health_status}</div><p class="muted">${s.source?'Source':'Service'} | ${s.port??'n/a'} | Restarts ${s.restart_count}</p><div class="actions"><button onclick="${s.source?`sourceAction('source_start','${name}')`:`action('start','${name}')`}">Start</button><button onclick="${s.source?`sourceAction('source_stop','${name}')`:`action('stop','${name}')`}">Stop</button><button onclick="${s.source?`sourceAction('source_restart','${name}')`:`action('restart','${name}')`}">Restart</button>${sourceActions}<button onclick="showLogs('${name}')">Logs</button></div></article>`;select.innerHTML+=`<option>${name}</option>`});if(selected)select.value=selected}
async function action(a,s){await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:a,service:s})});await refresh()}
function allAction(a){action(a,'all')}
async function sourceAction(a,s){await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:a,service:s})});await refresh()}
async function sendEvent(){const text=prompt('Event JSON');if(!text)return;try{const event=JSON.parse(text);const result=await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:'event',event})});alert(result.result||'Event sent')}catch(error){showError(error)}}
async function runTool(){const name=prompt('Tool name');if(!name)return;const text=prompt('Tool arguments JSON (or blank for {})')||'{}';try{const args=JSON.parse(text);const result=await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:'tool',name,args})});alert(result.result||'Tool completed')}catch(error){showError(error)}}
function toggleDebug(){request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:'debug',enabled:!state.debug_output})}).then(refresh)}
function toggleMonitor(){request('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({action:'monitor',enabled:!state.monitoring})}).then(refresh)}
function loadLogs(){showLogs(document.querySelector('#serviceSelect').value)}
async function showLogs(s){if(!s)return;document.querySelector('#serviceSelect').value=s;const d=await request('/api/logs/'+encodeURIComponent(s));document.querySelector('#logs').textContent=d.lines.join('\\n')||'No log entries.'}
function showError(error){document.querySelector('#summary').textContent=`Error: ${error.message}`;document.querySelector('#summary').className='bad'}
init().catch(showError);
</script>
"""


if __name__ == "__main__":
    dashboard = create_dashboard()
    dashboard.run(host=os.environ.get("ROBERT_DASHBOARD_HOST", "0.0.0.0"), port=int(os.environ.get("ROBERT_DASHBOARD_PORT", "8080")))

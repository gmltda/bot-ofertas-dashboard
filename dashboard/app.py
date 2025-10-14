import os
import sys
import json
import threading
import subprocess
from datetime import datetime

from flask import Flask, render_template, request, jsonify


# Diretórios e paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FAVORITOS_FILE = os.path.join(DATA_DIR, "favoritos.json")
MINED_TODAY_FILE = os.path.join(DATA_DIR, "mined_today.json")


app = Flask(__name__, template_folder="templates", static_folder="static")


# Estado do processo do minerador
PROCESS: subprocess.Popen | None = None
PROC_LOCK = threading.Lock()
STATUS = {"running": False}


def count_mined_today() -> int:
    """Conta quantas keywords foram mineradas hoje (baseado em mined_today.json JSONL)."""
    if not os.path.exists(MINED_TODAY_FILE):
        return 0
    hoje = datetime.now().strftime("%Y-%m-%d")
    count = 0
    try:
        with open(MINED_TODAY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts = obj.get("timestamp")
                    if isinstance(ts, str) and ts.split(" ")[0] == hoje:
                        count += 1
                except Exception:
                    # Ignora linhas inválidas
                    continue
    except Exception:
        return 0
    return count


def load_favoritos() -> list:
    if not os.path.exists(FAVORITOS_FILE):
        return []
    try:
        with open(FAVORITOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except Exception:
        return []


def save_favorito(item: dict) -> None:
    favoritos = load_favoritos()
    favoritos.append(item)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FAVORITOS_FILE, "w", encoding="utf-8") as f:
        json.dump(favoritos, f, ensure_ascii=False, indent=2)


def _monitor_proc(proc: subprocess.Popen) -> None:
    """Thread que monitora término do processo e atualiza o status."""
    try:
        proc.wait()
    finally:
        with PROC_LOCK:
            global PROCESS
            STATUS["running"] = False
            PROCESS = None


@app.route("/")
def index():
    stats = {
        "status": "ativo" if STATUS["running"] else "parado",
        "mined_count": count_mined_today(),
    }
    favoritos = load_favoritos()
    return render_template("index.html", stats=stats, favoritos=favoritos)


@app.route("/start", methods=["POST"]) 
def start():
    payload = request.get_json(silent=True) or {}
    mode = (payload.get("mode") or "").strip()
    keyword = (payload.get("keyword") or "").strip()
    if mode not in ("manual", "txt"):
        return jsonify({"msg": "Modo inválido"}), 400

    with PROC_LOCK:
        global PROCESS
        if STATUS["running"]:
            return jsonify({"msg": "Já existe um processo em execução"}), 400
        cmd = [sys.executable, os.path.join(BASE_DIR, "minerador.py"), "--mode", mode]
        if mode == "manual" and keyword:
            cmd += ["--keyword", keyword]
        os.makedirs(DATA_DIR, exist_ok=True)
        PROCESS = subprocess.Popen(cmd, cwd=BASE_DIR)
        STATUS["running"] = True
        t = threading.Thread(target=_monitor_proc, args=(PROCESS,), daemon=True)
        t.start()

    msg = f"🚀 Mineração iniciada em modo {'manual' if mode == 'manual' else 'txt'}!"
    return jsonify({"msg": msg})


@app.route("/stop", methods=["POST"]) 
def stop():
    with PROC_LOCK:
        global PROCESS
        if not STATUS["running"] or PROCESS is None:
            return jsonify({"msg": "Nenhum processo em execução"}), 400
        try:
            PROCESS.terminate()
            try:
                PROCESS.wait(timeout=2)
            except Exception:
                PROCESS.kill()
        finally:
            STATUS["running"] = False
            PROCESS = None
    return jsonify({"msg": "🛑 Processo interrompido!"})


@app.route("/favoritos", methods=["POST"]) 
def favoritos():
    payload = request.get_json(silent=True) or request.form
    keyword = (payload.get("keyword") or "").strip()
    page_name = (payload.get("page_name") or "").strip()
    ad_library_link = (payload.get("ad_library_link") or "").strip()
    if not keyword or not page_name or not ad_library_link:
        return jsonify({"msg": "Dados insuficientes"}), 400
    save_favorito({
        "keyword": keyword,
        "page_name": page_name,
        "ad_library_link": ad_library_link,
    })
    return jsonify({"msg": "⭐ Favorito salvo!"})


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
import os
import sys
import json
import threading
import subprocess
import signal
from datetime import datetime

# Garantir que o Playwright tenha o Chromium instalado
try:
    subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
except Exception as e:
    print("[WARN] Falha ao instalar Chromium automaticamente:", e)

from flask import Flask, request, jsonify
from flask_cors import CORS


# Base paths (Render.com service root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FAVORITOS_FILE = os.path.join(DATA_DIR, "favoritos.json")
MINED_TODAY_FILE = os.path.join(DATA_DIR, "mined_today.json")
os.makedirs(DATA_DIR, exist_ok=True)
FAVORITOS_PATH = os.path.join(DATA_DIR, "favoritos.json")

app = Flask(__name__)
CORS(app, origins=[
    "https://gmltda.github.io",
    "https://bot-oferta.vagalimitada.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
])


# Minerador subprocess state
PROCESS: subprocess.Popen | None = None
PROC_LOCK = threading.Lock()
STATUS = {"running": False}


def count_mined_today() -> int:
    """Count keywords mined today from mined_today.json (JSONL)."""
    if not os.path.exists(MINED_TODAY_FILE):
        return 0
    today = datetime.now().strftime("%Y-%m-%d")
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
                    if isinstance(ts, str) and ts.split(" ")[0] == today:
                        count += 1
                except Exception:
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
    favs = load_favoritos()
    favs.append(item)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FAVORITOS_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)


def _monitor_proc(proc: subprocess.Popen) -> None:
    try:
        proc.wait()
    finally:
        with PROC_LOCK:
            global PROCESS
            STATUS["running"] = False
            PROCESS = None


@app.route("/status", methods=["GET"]) 
def status():
    return jsonify({
        "status": "ativo" if STATUS["running"] else "parado",
        "mined_today": count_mined_today(),
    })


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


@app.route("/favoritos", methods=["GET", "POST"]) 
def favoritos():
    if request.method == "GET":
        if not os.path.exists(FAVORITOS_PATH):
            return jsonify({"favoritos": []})
        with open(FAVORITOS_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
        return jsonify({"favoritos": data})
    elif request.method == "POST":
        fav = request.get_json(force=True)
        if not os.path.exists(FAVORITOS_PATH):
            open(FAVORITOS_PATH, "w", encoding="utf-8").write("[]")
        with open(FAVORITOS_PATH, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
            data.append(fav)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({"msg": "⭐ Favorito salvo!"})


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

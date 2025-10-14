import argparse
import json
import os
import random
import time
from datetime import datetime
from typing import List, Dict, Optional

import requests


# ==========================
# Configuração Trello
# ==========================
TRELLO_KEY = os.getenv("TRELLO_KEY", "<SUA_TRELLO_KEY_AQUI>")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "<SEU_TRELLO_TOKEN_AQUI>")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID", "<SEU_TRELLO_LIST_ID_AQUI>")


# ==========================
# Paths do projeto (backend)
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KEYWORDS_FILE = os.path.join(DATA_DIR, "keywords.txt")
MINED_TODAY_FILE = os.path.join(DATA_DIR, "mined_today.json")
FAVORITOS_FILE = os.path.join(DATA_DIR, "favoritos.json")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
            f.write("bolsa de crochê\nmoldes de costura\nresina artística\nfeltro religioso\nbordado em pano de prato\n")
    if not os.path.exists(MINED_TODAY_FILE):
        with open(MINED_TODAY_FILE, "w", encoding="utf-8") as f:
            f.write("")
    if not os.path.exists(FAVORITOS_FILE):
        with open(FAVORITOS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")


def _read_json_lines(path: str) -> List[Dict]:
    items = []
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def _now_ts() -> float:
    return time.time()


def already_mined_last24(keyword: str) -> bool:
    entries = _read_json_lines(MINED_TODAY_FILE)
    cutoff = _now_ts() - 24 * 3600
    for e in entries:
        if e.get("keyword") == keyword and float(e.get("ts", 0)) >= cutoff:
            return True
    return False


def save_mined(keyword: str) -> None:
    entry = {
        "keyword": keyword,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ts": _now_ts(),
    }
    with open(MINED_TODAY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_keywords_txt() -> List[str]:
    if not os.path.exists(KEYWORDS_FILE):
        return []
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def enviar_para_trello(anuncio: Dict) -> Optional[str]:
    if not TRELLO_KEY or not TRELLO_TOKEN or not TRELLO_LIST_ID:
        print("[Trello] Configuração ausente (key/token/list id).")
        return None

    titulo = anuncio.get("titulo", "Anúncio Mineração")
    ad_library_link = anuncio.get("ad_library_link")
    landing_page_url = anuncio.get("landing_page_url")
    descricao = anuncio.get("descricao", "")
    if not descricao:
        descricao = f"Link da Ad Library: {ad_library_link}\nLanding page: {landing_page_url or 'N/A'}"

    try:
        resp = requests.post(
            "https://api.trello.com/1/cards",
            params={
                "key": TRELLO_KEY,
                "token": TRELLO_TOKEN,
                "idList": TRELLO_LIST_ID,
                "name": titulo,
                "desc": descricao,
            },
            timeout=15,
        )
        resp.raise_for_status()
        card = resp.json()
        card_id = card.get("id")
        card_url = card.get("shortUrl") or card.get("url")
        print(f"[Trello] Card criado: {card_url}")

        media_path = anuncio.get("media_path")
        if media_path and os.path.exists(media_path):
            with open(media_path, "rb") as f:
                files = {"file": (os.path.basename(media_path), f)}
                r2 = requests.post(
                    f"https://api.trello.com/1/cards/{card_id}/attachments",
                    params={"key": TRELLO_KEY, "token": TRELLO_TOKEN},
                    files=files,
                    timeout=30,
                )
                r2.raise_for_status()
                print(f"[Trello] Anexo enviado: {os.path.basename(media_path)}")
        return card_url
    except Exception as e:
        print(f"[Trello] Falha ao criar/editar card: {e}")
        return None


class BrowserSession:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            print("[Playwright] Não instalado. Rode 'pip install playwright' e 'python -m playwright install'.")
            return False
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        print("[Playwright] Navegador iniciado.")
        return True

    def stop(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("[Playwright] Navegador encerrado.")
        except Exception as e:
            print(f"[Playwright] Erro ao encerrar: {e}")


def minerar_keyword(keyword: str, session: BrowserSession) -> List[Dict]:
    anuncios: List[Dict] = []
    try:
        if session and session.context:
            page = session.context.new_page()
            ad_url = f"https://www.facebook.com/ads/library/?q={requests.utils.quote(keyword)}"
            page.goto(ad_url)
            time.sleep(random.uniform(1.5, 3.0))
            media_candidate = None
            for candidate in [
                os.path.join(DATA_DIR, "creative.jpg"),
                os.path.join(DATA_DIR, "media", "creative.jpg"),
            ]:
                if os.path.exists(candidate):
                    media_candidate = candidate
                    break
            anuncios.append({
                "titulo": f"Oferta: {keyword}",
                "descricao": f"Keyword minerada: {keyword}\nAd Library: {ad_url}",
                "ad_library_link": ad_url,
                "landing_page_url": ad_url,
                "score": 90,
                "media_path": media_candidate,
            })
    except Exception as e:
        print(f"[Minerador] Erro ao minerar '{keyword}': {e}")
    return anuncios


def run_manual(keyword: str) -> None:
    if not keyword:
        print("[Minerador] Keyword não informada para modo manual.")
        return
    if already_mined_last24(keyword):
        print(f"[Minerador] Ignorado (já minerado nas últimas 24h): {keyword}")
        return
    session = BrowserSession()
    started = session.start()
    try:
        anuncios = minerar_keyword(keyword, session if started else None)
        if anuncios:
            for a in anuncios:
                enviar_para_trello(a)
        save_mined(keyword)
        print(f"[Minerador] Finalizado manual: {keyword}")
    finally:
        session.stop()


def run_txt(stop_event: Optional[object] = None) -> None:
    keywords = read_keywords_txt()
    if not keywords:
        print("[Minerador] Nenhuma keyword em data/keywords.txt")
        return
    session = BrowserSession()
    started = session.start()
    try:
        for kw in keywords:
            if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
                print("[Minerador] Stop solicitado, encerrando...")
                break
            if already_mined_last24(kw):
                print(f"[Minerador] Ignorado (24h): {kw}")
                continue
            anuncios = minerar_keyword(kw, session if started else None)
            for a in anuncios:
                enviar_para_trello(a)
            save_mined(kw)
            delay = random.uniform(5, 10)
            print(f"[Minerador] Aguardando {delay:.1f}s antes do próximo...")
            time.sleep(delay)
        print("[Minerador] Modo TXT finalizado.")
    finally:
        session.stop()


def start_from_args():
    ensure_data_dir()
    parser = argparse.ArgumentParser(description="Bot Minerador de Ofertas")
    parser.add_argument("--mode", choices=["manual", "txt"], required=True)
    parser.add_argument("--keyword", required=False)
    args = parser.parse_args()
    if args.mode == "manual":
        run_manual(args.keyword)
    elif args.mode == "txt":
        run_txt()


if __name__ == "__main__":
    start_from_args()
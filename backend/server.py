"""
server.py — Catalyst AppSail entry point
Serves the dashboard as static files and runs two background schedulers:
  1. General data fetcher (App Store, Play Store, News) — every 5 min
  2. Twitter screenshotter (Playwright + Catalyst upload)  — every 15 min

KEY BEHAVIOUR (v2 — incremental X post merge):
  - twitter_fetcher.run_twitter_cycle() now MERGES new posts with previously
    saved ones (dedup by URL, sort newest-first, keep top 5).
  - data.json is written to both /tmp (runtime) AND backend/data.json (durable).
  - On Catalyst restart, server.py seeds /tmp/data.json from backend/data.json
    so the frontend always has stale-but-valid data while the first scrape runs.
"""

import os
import threading
import time
import logging
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
import requests as req_lib
from bs4 import BeautifulSoup
import json
import base64

# ── Import data fetcher ───────────────────────────────────
from z1 import run_fetch_cycle, now

# ── Import Twitter screenshotter ─────────────────────────
try:
    from twitter_fetcher import run_twitter_cycle
    _TWITTER_AVAIL = True
except ImportError as _te:
    _TWITTER_AVAIL = False
    print(f"[server] WARNING: twitter_fetcher not available: {_te}")

# ── Import AI review analysis blueprint ──────────────────
from ai_review_analysis import analysis_bp

# ── Directory Setup ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

if os.name == "nt":
    DATA_DIR     = str(BASE_DIR)
    SESSION_FILE = os.path.join(BASE_DIR, "x_session.json")
else:
    DATA_DIR     = "/tmp"
    SESSION_FILE = "/tmp/x_session.json"

# ── Twitter Session Restoration ──
X_SESSION_DATA = os.getenv("X_SESSION_DATA")
if X_SESSION_DATA:
    try:
        with open(SESSION_FILE, "w") as f:
            f.write(X_SESSION_DATA)
        print(f"[inf] [Secure] Restored X session to {SESSION_FILE}")
    except Exception as e:
        print(f"[err] [Secure] Failed to restore X session: {e}")

app = Flask(__name__, static_folder="public", static_url_path="")
CORS(app)
app.register_blueprint(analysis_bp)

# ── Logging ──────────────────────────────────────────────
log_file = os.path.join(DATA_DIR, "app.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ── Helper: load data.json with fallbacks ─────────────────
def _load_data_json():
    """
    Try data.json from multiple locations in priority order:
      1. /tmp/data.json         — runtime (most current)
      2. backend/data.json      — durable backup written by twitter_fetcher
      3. public/data.json       — Vite dev fallback
    Returns the path of the first file that exists and is non-empty.
    """
    candidates = [
        os.path.join(DATA_DIR, "data.json"),
        os.path.join(BASE_DIR, "data.json"),
        os.path.join(PUBLIC_DIR, "data.json"),
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 10:
            return path
    return None


# ── Routes ────────────────────────────────────────────────

@app.route("/logs")
@app.route("/api/logs")
def view_logs():
    """Endpoint to view the last 100 lines of logs in the browser."""
    if not os.path.exists(log_file):
        return "Log file not created yet. The system is still booting up... Please refresh in 30 seconds.", 200
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "Log file exists but is currently empty. Waiting for the first background task to start...", 200
            return Response("".join(lines[-100:]), mimetype="text/plain")
    except Exception as e:
        return f"Error reading logs: {e}", 500


@app.route("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/data.json")
@app.route("/data")
def data_json():
    """Serve data.json — checks /tmp first, then backend dir, then public dir."""
    data_path = _load_data_json()
    if data_path:
        directory = os.path.dirname(data_path)
        filename  = os.path.basename(data_path)
        return send_from_directory(directory, filename)
    return jsonify({"error": "data.json not found yet"}), 404


@app.route("/api/data/<path:filename>")
@app.route("/data/<path:filename>")
def serve_backend_files(filename):
    """
    Serve screenshots or other backend-generated files.
    Priority:
      1. File exists on disk (/tmp or backend dir)
      2. Serve inline base64 from twitter.inline_screenshots in data.json
    """
    # Check /tmp first, then backend dir
    for search_dir in [DATA_DIR, BASE_DIR]:
        disk_path = os.path.join(search_dir, filename)
        if os.path.exists(disk_path):
            return send_from_directory(search_dir, filename)

    # Fallback: serve inline base64 from data.json
    try:
        data_path = _load_data_json()
        if data_path:
            with open(data_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)

            tw         = payload.get("twitter", {})
            inline_map = tw.get("inline_screenshots", {})
            data_url   = inline_map.get(filename, "")

            if isinstance(data_url, str) and data_url.startswith("data:image/"):
                mime = "image/png" if ".png" in filename.lower() else "image/jpeg"
                b64  = data_url.split(",", 1)[1]
                return Response(base64.b64decode(b64), mimetype=mime)
    except Exception as e:
        log.error(f"[server] Inline serve failed for {filename}: {e}")

    return jsonify({"error": "file not found", "file": filename}), 404


def resolve_google_news_url(url):
    """Decode Google News CBM base64 URL to get the real article URL."""
    import base64 as _b64, re
    try:
        if "/articles/CBM" in url:
            cbm = url.split("/articles/")[1].split("?")[0]
            cbm += "=" * ((4 - len(cbm) % 4) % 4)
            raw  = _b64.urlsafe_b64decode(cbm)
            urls = re.findall(b"https?://[^\x00-\x20\"'<>]+", raw)
            if urls:
                return urls[-1].decode("utf-8", errors="ignore")
    except Exception:
        pass
    try:
        r = req_lib.get(
            url, timeout=10, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        final = r.url
        if "google.com" in final:
            soup = BeautifulSoup(r.text, "html.parser")
            a = soup.find("a")
            if a and a.get("href", "").startswith("http"):
                return a["href"]
        return final
    except Exception:
        return url


@app.route("/meta")
def fetch_meta():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        if "news.google.com" in url or "google.com/articles" in url:
            url = resolve_google_news_url(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        r    = req_lib.get(url, timeout=10, allow_redirects=True, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        def og(prop):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return tag["content"].strip() if tag and tag.get("content") else ""

        def meta_name(name):
            tag = soup.find("meta", attrs={"name": name})
            return tag["content"].strip() if tag and tag.get("content") else ""

        title = og("og:title") or og("twitter:title") or (soup.title.string.strip() if soup.title else "")
        desc  = meta_name("description") or og("og:description") or og("twitter:description")
        image = og("og:image") or og("twitter:image")
        if image and "google.com" in image:
            image = ""

        for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                         "iframe", "noscript", "form", "button"]):
            tag.decompose()

        blocks = []
        article_root = (
            soup.find("article")
            or soup.find(attrs={"itemprop": "articleBody"})
            or soup.find(
                class_=lambda c: c and any(
                    x in c for x in ["article-body", "article__body", "story-body",
                                     "post-body", "entry-content", "content-body",
                                     "article-content", "articleBody"]
                )
            )
            or soup.find("main")
            or soup.body
        )

        if article_root:
            for el in article_root.find_all(
                ["h1", "h2", "h3", "h4", "p", "figure", "img", "blockquote"], recursive=True
            ):
                tag = el.name
                if tag in ("h1", "h2", "h3", "h4"):
                    txt = el.get_text().strip()
                    if txt and len(txt) > 3:
                        blocks.append({"type": "heading", "level": int(tag[1]), "text": txt})
                elif tag == "p":
                    txt = el.get_text().strip()
                    if len(txt) > 40:
                        blocks.append({"type": "paragraph", "text": txt})
                elif tag == "blockquote":
                    txt = el.get_text().strip()
                    if len(txt) > 20:
                        blocks.append({"type": "quote", "text": txt})
                elif tag in ("figure", "img"):
                    img_el = el if tag == "img" else el.find("img")
                    if not img_el:
                        continue
                    src = img_el.get("src") or img_el.get("data-src") or ""
                    if src and not src.startswith("data:") and len(src) > 10:
                        if src.startswith("//"):
                            src = "https:" + src
                        elif src.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(r.url)
                            src = f"{parsed.scheme}://{parsed.netloc}{src}"
                        cap_el  = el.find("figcaption") if tag == "figure" else None
                        caption = cap_el.get_text().strip() if cap_el else (img_el.get("alt", "") or "")
                        blocks.append({"type": "image", "src": src, "caption": caption})

        seen, deduped = set(), []
        for b in blocks:
            val = b.get("text") or b.get("src") or ""
            key = str(val)[:120]
            if key not in seen:
                seen.add(key)
                deduped.append(b)

        full_body = "\n\n".join(
            str(b.get("text", "")) for b in deduped if b.get("type") == "paragraph"
        ) or desc

        import re as _re
        if desc and title:
            escaped = _re.escape(title[:60])
            desc = _re.sub(r"^" + escaped + r"[\s\-\u2013\u2014:.|]*", "", desc, flags=_re.IGNORECASE).strip()

        return jsonify({
            "title":       title,
            "description": desc,
            "body":        full_body,
            "image":       image,
            "url":         r.url,
            "blocks":      deduped,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": now()})


@app.route("/trigger-fetch")
def trigger_fetch():
    """Manual trigger — force a full data refresh."""
    thread = threading.Thread(target=run_fetch_cycle, daemon=True)
    thread.start()
    return jsonify({"status": "fetch started", "time": now()})


# ── Global thread lock for Twitter to prevent duplicates ─
_TWITTER_BUSY = False
_TWITTER_LOCK = threading.Lock()


@app.route("/x-session/status")
def x_session_status():
    """Check if X session exists and is valid."""
    from twitter_fetcher import _validate_session_file
    is_valid = _validate_session_file()
    return jsonify({
        "has_session": is_valid,
        "session_file": str(SESSION_FILE),
        "message": "Session found ✓" if is_valid else "No valid session — please log in",
        "login_url": "/x-session/login",
    })


@app.route("/x-session/login")
def x_session_login():
    """Start interactive X login (headful browser). Visit this URL to log in manually."""
    from twitter_fetcher import _validate_session_file, _save_session, run_twitter_cycle

    if _validate_session_file():
        return jsonify({
            "status": "already_logged_in",
            "message": "✓ Valid session exists. Ready to fetch posts.",
            "session_file": str(SESSION_FILE),
            "next_action": "Visit /trigger-twitter to fetch and screenshot posts",
        }), 200

    def _interactive_login():
        try:
            from playwright.sync_api import sync_playwright
            import time as time_lib

            log.info("[X-Login] Starting interactive login browser...")

            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                          "--disable-gpu", "--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                )
                page = context.new_page()
                page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)
                log.info("[X-Login] ✓ Browser opened. Waiting for login (180 seconds timeout)...")
                time_lib.sleep(180)

                log.info("[X-Login] Saving authenticated session...")
                if _save_session(context):
                    log.info("[X-Login] ✓ Session saved successfully")
                    global _TWITTER_BUSY
                    if not _TWITTER_BUSY:
                        try:
                            _TWITTER_BUSY = True
                            run_twitter_cycle()
                            log.info("[X-Login] ✓ Twitter fetch complete")
                        except Exception as e:
                            log.error(f"[X-Login] Auto-fetch failed: {e}")
                        finally:
                            _TWITTER_BUSY = False
                else:
                    log.error("[X-Login] Failed to save session")

                browser.close()

        except Exception as e:
            log.error(f"[X-Login] Interactive login error: {e}", exc_info=True)

    login_thread = threading.Thread(target=_interactive_login, daemon=True)
    login_thread.start()

    return jsonify({
        "status": "login_started",
        "message": "✓ Login flow started. Please complete login via X.",
        "instructions": [
            "1. A browser window will open shortly",
            "2. Log in with your X account credentials",
            "3. Complete all login steps (including 2FA if prompted)",
            "4. Wait for browser to auto-close (~3 minutes timeout)",
            "5. Session will be saved automatically",
        ],
        "session_file": str(SESSION_FILE),
        "check_status_url": "/x-session/status",
        "trigger_fetch_url": "/trigger-twitter",
        "time": now(),
    }), 202


@app.route("/trigger-twitter")
def trigger_twitter():
    """Manual trigger — force a Twitter screenshot refresh immediately."""
    from twitter_fetcher import _validate_session_file

    if not _validate_session_file():
        return jsonify({
            "status": "no_valid_session",
            "message": "No authenticated X session found. Visit /x-session/login to log in and save session",
            "login_url": "/x-session/login",
            "session_check_url": "/x-session/status",
        }), 401

    global _TWITTER_BUSY
    if not _TWITTER_AVAIL:
        return jsonify({"status": "error", "message": "twitter_fetcher not available"}), 503

    with _TWITTER_LOCK:
        if _TWITTER_BUSY:
            return jsonify({
                "status": "already_running",
                "message": "Twitter fetch already in progress. Please wait.",
                "time": now()
            }), 429
        _TWITTER_BUSY = True

    def _manual_wrapper():
        global _TWITTER_BUSY
        try:
            run_twitter_cycle()
        finally:
            with _TWITTER_LOCK:
                _TWITTER_BUSY = False

    thread = threading.Thread(target=_manual_wrapper, daemon=True)
    thread.start()
    return jsonify({"status": "twitter fetch started", "time": now()})


# ── Scheduler intervals ───────────────────────────────────
FETCH_INTERVAL_MINUTES   = 5
TWITTER_INTERVAL_MINUTES = 15


def scheduler_loop():
    log.info(f"[scheduler] General fetcher starting. Interval: {FETCH_INTERVAL_MINUTES} min.")
    try:
        time.sleep(5)
        run_fetch_cycle()
    except Exception as e:
        log.error(f"[scheduler] Initial fetch failed: {e}")
    while True:
        time.sleep(FETCH_INTERVAL_MINUTES * 60)
        try:
            run_fetch_cycle()
        except Exception as e:
            log.error(f"[scheduler] Fetch cycle failed: {e}")


def twitter_scheduler_loop():
    """
    Runs the Twitter screenshot + merge cycle every 15 minutes.
    New posts are merged on top of old ones (top 5 kept, newest first).
    """
    if not _TWITTER_AVAIL:
        log.warning("[twitter-scheduler] twitter_fetcher unavailable – thread exiting.")
        return

    log.info(f"[twitter-scheduler] Starting. Interval: {TWITTER_INTERVAL_MINUTES} min.")
    try:
        time.sleep(15)
        run_twitter_cycle()
    except Exception as e:
        log.error(f"[twitter-scheduler] Initial Twitter fetch failed: {e}")

    while True:
        time.sleep(TWITTER_INTERVAL_MINUTES * 60)
        try:
            run_twitter_cycle()
        except Exception as e:
            log.error(f"[twitter-scheduler] Twitter cycle failed: {e}")


def _chromium_ready():
    """Check if Playwright Chromium binary actually exists on disk."""
    import glob
    pw_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/tmp/pw-browsers")
    matches = glob.glob(f"{pw_path}/**/chrome-headless-shell", recursive=True) + \
              glob.glob(f"{pw_path}/**/chromium", recursive=True) + \
              glob.glob(f"{pw_path}/**/chrome", recursive=True)
    return bool(matches)


def start_background_scheduler():
    """
    Initialize background tasks on Catalyst AppSail:
    1. Seed /tmp/data.json from backend/data.json if /tmp is empty (fresh container).
    2. If X session + Chromium both available, run initial Twitter fetch.
    3. Start general (5 min) and Twitter (15 min) scheduler loops.
    """
    import shutil as _shutil
    global _TWITTER_BUSY

    # ── Seed /tmp/data.json from durable backend/data.json ──────────────────
    # Catalyst containers start with a fresh /tmp every deployment.
    # twitter_fetcher writes to BOTH /tmp/data.json AND backend/data.json.
    # On the next boot we copy backend/data.json → /tmp/data.json so the
    # frontend immediately has last-known posts while the first scrape runs.
    tmp_data     = os.path.join(DATA_DIR, "data.json")     # /tmp/data.json
    backend_data = os.path.join(BASE_DIR, "data.json")     # backend/data.json
    if not os.path.exists(tmp_data) and os.path.exists(backend_data):
        try:
            _shutil.copy2(backend_data, tmp_data)
            log.info(f"[startup] ✓ Seeded {tmp_data} from {backend_data} (fresh container)")
        except Exception as e:
            log.warning(f"[startup] Could not seed data.json: {e}")

    # ── Check X session + Chromium before auto-fetching ──────────────────────
    session_file = Path("/tmp/x_session.json") if os.path.exists("/tmp/x_session.json") else Path(BASE_DIR) / "x_session.json"
    chromium_ok  = _chromium_ready()

    if session_file.exists() and _TWITTER_AVAIL and chromium_ok:
        log.info("[startup] ✓ X session + Chromium found! Auto-fetching Twitter data...")
        try:
            _TWITTER_BUSY = True
            run_twitter_cycle()
            log.info("[startup] ✓ Initial Twitter fetch complete.")
        except Exception as e:
            log.error(f"[startup] Initial Twitter fetch failed: {e}")
        finally:
            _TWITTER_BUSY = False
    elif not chromium_ok:
        log.warning("[startup] ⚠️  Chromium not ready yet — skipping startup fetch. Scheduler will retry in 15 min.")
    elif not session_file.exists():
        log.warning("[startup] ⚠️  No X session found. Visit /x-session/login to set up.")

    # ── General data fetcher thread ──
    t1 = threading.Thread(target=scheduler_loop, daemon=True, name="fetcher-scheduler")
    t1.start()
    log.info("[scheduler] General fetcher thread launched.")

    # ── Twitter screenshot thread ──
    t2 = threading.Thread(target=twitter_scheduler_loop, daemon=True, name="twitter-scheduler")
    t2.start()
    log.info("[twitter-scheduler] Twitter screenshot thread launched.")


# ── Dev server ────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n[server] Arattai local server starting…")
    print(f"[server] URL: http://127.0.0.1:5050")
    print(f"[server] Manual Twitter refresh: http://127.0.0.1:5050/trigger-twitter\n")
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)

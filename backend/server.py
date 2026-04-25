"""
server.py — Catalyst AppSail entry point
Serves the dashboard as static files and runs two background schedulers:
  1. General data fetcher (App Store, Play Store, News) — every 5 min
  2. Twitter screenshotter (Playwright + Catalyst upload)  — every 15 min
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

if os.name == "nt":
    DATA_DIR = str(BASE_DIR)
    SESSION_FILE = os.path.join(BASE_DIR, "x_session.json")
else:
    DATA_DIR = "/tmp"
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

import json
import base64

# Configure logging to console AND file for the web viewer
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

# ── Routes ────────────────────────────────────────────────
@app.route("/logs")
@app.route("/api/logs")
def view_logs():
    """Endpoint to view the last 100 lines of logs in the browser."""
    if not os.path.exists(log_file):
        return "Log file not created yet. Please wait for the first fetch cycle.", 200
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Return last 100 lines
            return Response("".join(lines[-100:]), mimetype="text/plain")
    except Exception as e:
        return f"Error reading logs: {e}", 500
@app.route("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")

@app.route("/data.json")
@app.route("/data")
def data_json():
    tmp_path = os.path.join(DATA_DIR, "data.json")
    if os.path.exists(tmp_path):
        return send_from_directory(DATA_DIR, "data.json")
    return send_from_directory(BASE_DIR, "data.json")

@app.route("/api/data/<path:filename>")
@app.route("/data/<path:filename>")
def serve_backend_files(filename):
    """Serve screenshots or other backend-generated files."""
    # Prioritize /tmp on Linux, or BASE_DIR on Windows
    disk_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(disk_path):
        return send_from_directory(DATA_DIR, filename)

    # Fallback: serve inline base64 data from data.json
    try:
        data_path = os.path.join(DATA_DIR, "data.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            
            # The structure is twitter -> inline_screenshots
            tw = payload.get("twitter", {})
            inline_map = tw.get("inline_screenshots", {})
            data_url = inline_map.get(filename, "")
            
            if isinstance(data_url, str) and data_url.startswith("data:image/"):
                mime = "image/png" if ".png" in filename.lower() else "image/jpeg"
                b64 = data_url.split(",", 1)[1]
                return Response(base64.b64decode(b64), mimetype=mime)
    except Exception as e:
        log.error(f"[server] Inline serve failed for {filename}: {e}")

    return jsonify({"error": "file not found", "file": filename}), 404


def resolve_google_news_url(url):
    """Decode Google News CBM base64 URL to get the real article URL."""
    import base64, re
    try:
        if "/articles/CBM" in url:
            cbm = url.split("/articles/")[1].split("?")[0]
            cbm += "=" * ((4 - len(cbm) % 4) % 4)
            raw  = base64.urlsafe_b64decode(cbm)
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
    from pathlib import Path
    session_file = Path(BASE_DIR) / "x_session.json"
    is_valid = _validate_session_file()
    return jsonify({
        "has_session": is_valid,
        "session_file": str(session_file),
        "message": "Session found ✓" if is_valid else "No valid session — please log in",
        "login_url": "/x-session/login",
    })


@app.route("/x-session/login")
def x_session_login():
    """Start interactive X login (headful browser). Visit this URL to log in manually."""
    from pathlib import Path
    from twitter_fetcher import _validate_session_file, _save_session, run_twitter_cycle
    import json as json_lib
    # Check if already logged in with valid session
    if _validate_session_file():
        return jsonify({
            "status": "already_logged_in",
            "message": "✓ Valid session exists. Ready to fetch posts.",
            "session_file": str(SESSION_FILE),
            "next_action": "Visit /trigger-twitter to fetch and screenshot posts",
        }), 200
    
    # Start login in background thread
    def _interactive_login():
        try:
            from playwright.sync_api import sync_playwright
            import time as time_lib
            
            log.info("[X-Login] Starting interactive login browser...")
            
            with sync_playwright() as pw:
                # Headful browser for manual login
                browser = pw.chromium.launch(
                    headless=True,  # Always headless on server — use cookie upload instead
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--start-maximized", "--disable-blink-features=AutomationControlled"],
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
                log.info("[X-Login] ✓ Browser opened. Waiting for user login (180 seconds timeout)...")
                
                # Wait for user to complete login
                time_lib.sleep(180)
                
                # Save session using proper method
                log.info("[X-Login] Saving authenticated session...")
                if _save_session(context):
                    log.info("[X-Login] ✓ Session saved successfully")
                    # Auto-trigger Twitter fetch to capture screenshots
                    log.info("[X-Login] Auto-triggering Twitter fetch with screenshots...")
                    global _TWITTER_BUSY
                    if not _TWITTER_BUSY:
                        try:
                            _TWITTER_BUSY = True
                            run_twitter_cycle()
                            log.info("[X-Login] ✓ Twitter fetch and screenshot capture complete")
                        except Exception as e:
                            log.error(f"[X-Login] Auto-fetch failed: {e}")
                        finally:
                            _TWITTER_BUSY = False
                else:
                    log.error("[X-Login] Failed to save session")
                
                browser.close()
                log.info("[X-Login] Browser closed")
                
        except Exception as e:
            log.error(f"[X-Login] Interactive login error: {e}", exc_info=True)
    
    # Run in background thread
    login_thread = threading.Thread(target=_interactive_login, daemon=True)
    login_thread.start()
    
    return jsonify({
        "status": "login_started",
        "message": "✓ Browser window will open in 2-3 seconds. Please log in to X.",
        "instructions": [
            "1. A browser window will open shortly",
            "2. Log in with your X account credentials",
            "3. Complete all login steps (including 2FA if prompted)",
            "4. Wait for browser to auto-close (~3 minutes timeout)",
            "5. Session will be saved automatically",
            "6. Screenshots will be captured on first fetch",
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
    from pathlib import Path
    
    # Check if valid session exists
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
                "message": "Twitter fetch already in progress. Please wait for current cycle to finish.",
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

# ── Background scheduler: general data (every 5 min) ─────
FETCH_INTERVAL_MINUTES   = 5
# ── Background scheduler: Twitter screenshots (every 15 min) ─
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
    Runs the Twitter screenshot cycle every 15 minutes:
      1. Fetch 5 recent @Arattai posts + screenshots
      2. Upload screenshots to Catalyst (delete previous)
      3. Update data.json
    """
    if not _TWITTER_AVAIL:
        log.warning("[twitter-scheduler] twitter_fetcher unavailable – thread exiting.")
        return

    log.info(f"[twitter-scheduler] Starting. Interval: {TWITTER_INTERVAL_MINUTES} min.")

    # Initial run with a short delay to let the main fetch settle first
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
    pw_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/app/pw-browsers")
    matches = glob.glob(f"{pw_path}/**/chrome-headless-shell", recursive=True) + \
              glob.glob(f"{pw_path}/**/chromium", recursive=True) + \
              glob.glob(f"{pw_path}/**/chrome", recursive=True)
    return bool(matches)


def start_background_scheduler():
    """
    Initialize background tasks:
    1. Check if X session exists on startup
    2. If yes, AND Chromium is ready, immediately fetch Twitter data
    3. Start regular schedulers (general data every 5min, Twitter every 15min)
    """
    global _TWITTER_BUSY

    # ── On startup: Check session AND Chromium before fetching ──
    # Check /tmp first (written from X_SESSION_JSON env var), then backend dir
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


# ── Schedulers are started by main.py after server binds ─


# ── Dev server ────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n[server] Arattai local server starting…")
    print(f"[server] URL: http://127.0.0.1:5050")
    print(f"[server] Manual Twitter refresh: http://127.0.0.1:5050/trigger-twitter\n")
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)

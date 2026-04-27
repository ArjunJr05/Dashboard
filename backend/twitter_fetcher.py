"""
twitter_fetcher.py
==================
Logs into X (Twitter) with provided credentials, navigates to @Arattai,
captures screenshots of the 5 most recent posts, scrapes top 5 comments
per post, uploads everything to Zoho Catalyst File Store (deleting stale
files first), then writes the result into data.json.

Schedule: called every 15 minutes from server.py

POST MERGE LOGIC (v2):
  - New posts fetched from X are merged with previously saved posts by URL.
  - Dedup by URL → sort newest-first by datetime → keep top 5.
  - If post 0 becomes post 2 (because 2 new posts arrived), its screenshot
    + inline image data is carried over from prev_twitter, NOT discarded.
  - inline_screenshots map is accumulated: old entries survive unless the
    post that owns them is evicted from the top-5.
"""

import os
import json
import time
import logging
import re
import base64
import urllib.request as _urlreq
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

# ── Force Playwright browser path — must be set before playwright imports ──
# Docker: /app/pw-browsers (set in Dockerfile ENV), Catalyst: /tmp/pw-browsers
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/app/pw-browsers")
os.environ.setdefault("HOME", "/root")

# ── Playwright (sync) ─────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    _PW_AVAIL = True
except ImportError:
    _PW_AVAIL = False
    import subprocess as _sp_mod, sys as _sys_mod
    try:
        print("[twitter-fetcher] playwright not found — attempting pip install...")
        _sp_mod.run([_sys_mod.executable, "-m", "pip", "install", "playwright", "--quiet"],
                    capture_output=True, check=False)
        _sp_mod.run([_sys_mod.executable, "-m", "playwright", "install", "chromium", "--with-deps"],
                    capture_output=True, check=False, timeout=300)
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        _PW_AVAIL = True
        print("[twitter-fetcher] ✓ playwright installed and imported successfully")
    except Exception as _pw_err:
        print(f"[twitter-fetcher] ERROR: playwright still not available after install attempt: {_pw_err}")
        _PW_AVAIL = False

# ── Zoho Catalyst SDK ─────────────────────────────────────
try:
    import zcatalyst_sdk
    _CATALYST_AVAIL = True
    print("[twitter-fetcher] zcatalyst-sdk loaded OK")
except ImportError:
    _CATALYST_AVAIL = False
    print("[twitter-fetcher] WARNING: zcatalyst-sdk not found")

# ── LLM enrichment (timing for X comments) ───────────────
try:
    from enrich_reviews import enrich_twitter_comments
    _ENRICH_AVAIL = True
except ImportError as _ee:
    _ENRICH_AVAIL = False
    print(f"[twitter-fetcher] WARNING: enrich_reviews not available: {_ee}")

# ══════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════
X_EMAIL    = "arattaitv@gmail.com"
X_USERNAME = "arattaitv"
X_PASSWORD = "Arattai@2006"
X_PROFILE  = "https://x.com/Arattai"

# Zoho Catalyst File Store folder ID
CATALYST_FOLDER_ID = "28618000000101001"
PROJECT_ID         = "28618000000061001"

_BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR     = str(_BACKEND_DIR) if os.name == "nt" else "/tmp"
DATA_FILE    = os.path.join(DATA_DIR, "data.json")

# ── Session file: prefer env var X_SESSION_JSON, then /tmp, then backend dir ──
def _get_session_path():
    """Write session JSON from env var to /tmp if available, return path."""
    env_json = os.environ.get("X_SESSION_DATA", os.environ.get("X_SESSION_JSON", "")).strip()
    if env_json:
        dest = "/tmp/x_session.json"
        try:
            data = json.loads(env_json)
            if isinstance(data, dict) and "cookies" in data:
                cookies = data["cookies"]
                for c in cookies:
                    if "expirationDate" in c:
                        c["expires"] = c.pop("expirationDate")
                    ss = str(c.get("sameSite", "")).lower()
                    if ss in ["lax", "strict", "none"]:
                        c["sameSite"] = ss.capitalize()
                    else:
                        c["sameSite"] = "None"
                data = {"cookies": cookies, "origins": []}
            with open(dest, "w") as f:
                json.dump(data, f)
            return dest
        except Exception as e:
            print(f"[twitter-fetcher] WARNING: Could not parse/write session data: {e}")
    if os.path.exists("/tmp/x_session.json"):
        return "/tmp/x_session.json"
    local = str(_BACKEND_DIR / "x_session.json")
    return local if os.path.exists(local) else None

# ══════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("twitter-fetcher")


def _local_file_url(path):
    """Return backend-served URL for a local screenshot path."""
    return f"/api/data/{os.path.basename(path)}"


def _file_to_data_url(path):
    """Inline image bytes as a data URL. Automatically compresses to JPEG to save RAM."""
    try:
        if not os.path.exists(path):
            return ""
        with Image.open(path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            if img.width > 1280:
                ratio = 1280 / float(img.width)
                new_height = int(float(img.height) * ratio)
                img = img.resize((1280, new_height), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        log.warning(f"Data URL conversion/compression failed for {path}: {e}")
        return ""


def _remote_tweet_screenshot(tweet_url):
    """Fallback screenshot provider for a tweet URL when local files are unavailable."""
    if not tweet_url:
        return ""
    clean = tweet_url.strip()
    return f"https://image.thum.io/get/width/1200/noanimate/{clean}"


# ──────────────────────────────────────────────────────────
#  CATALYST UPLOAD
# ──────────────────────────────────────────────────────────

def _catalyst_upload(file_paths):
    local_urls = [_local_file_url(p) for p in file_paths]
    prod_fallback_urls = ["" for _ in file_paths]

    if not _CATALYST_AVAIL:
        if os.name == "nt":
            log.warning("zcatalyst-sdk not available – using local screenshot URLs for dev.")
            return local_urls
        log.warning("zcatalyst-sdk not available in production – using inline screenshot fallback.")
        return prod_fallback_urls

    default_upload = "1" if os.name != "nt" else "0"
    if os.environ.get("ENABLE_CATALYST_UPLOAD", default_upload) != "1":
        if os.name == "nt":
            log.info("Catalyst upload disabled via ENABLE_CATALYST_UPLOAD. Using local screenshot URLs for dev.")
            return local_urls
        log.info("Catalyst upload disabled in production. Using inline screenshot fallback.")
        return prod_fallback_urls

    urls = []
    try:
        sdk_app = zcatalyst_sdk.initialize()
        fs      = sdk_app.filestore()
        folder  = fs.folder(CATALYST_FOLDER_ID)
        try:
            old_files = folder.get_files()
            for f in old_files:
                try:
                    folder.file(f.get_file_id()).delete()
                    log.info(f"Deleted old Catalyst file: {f.get_file_id()}")
                except Exception as e:
                    log.warning(f"Delete failed {f.get_file_id()}: {e}")
        except Exception as e:
            log.warning(f"Could not list folder files: {e}")
        for path in file_paths:
            if not os.path.exists(path):
                urls.append("")
                continue
            try:
                uploaded = folder.upload_file(path)
                file_id  = uploaded.get_file_id()
                api_base = os.environ.get("CATALYST_API_BASE", "https://api.catalyst.zoho.in").rstrip("/")
                dl_url   = (
                    f"{api_base}/baas/v1/project/{PROJECT_ID}"
                    f"/filestore/{CATALYST_FOLDER_ID}/file/{file_id}/download"
                )
                urls.append(dl_url)
                log.info(f"Uploaded {os.path.basename(path)} → file_id={file_id}")
            except Exception as e:
                log.error(f"Upload failed {path}: {e}")
                urls.append("" if os.name != "nt" else _local_file_url(path))
    except Exception as e:
        err = str(e)
        if "Catalyst headers are empty" in err:
            log.warning("Catalyst headers are empty in this runtime.")
        else:
            log.error(f"Catalyst SDK initialization error: {e}")
        urls = local_urls if os.name == "nt" else prod_fallback_urls
    return urls


# ──────────────────────────────────────────────────────────
#  X LOGIN
# ──────────────────────────────────────────────────────────

def _login(page):
    """Robust X login with fallback to guest view."""
    try:
        log.info("Navigating to X login flow ...")
        page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)

        log.info("Attempting standard email/password login ...")
        email_field = None
        for selector in [
            'input[autocomplete="username"]',
            'input[type="text"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="phone" i]',
            'input[data-testid="LoginForm_UserIdentifierField_TextField"]',
            'input[name="text"]',
        ]:
            try:
                email_field = page.query_selector(selector)
                if email_field:
                    log.info(f"Found email field with selector: {selector}")
                    break
            except:
                pass

        if not email_field:
            log.warning("Email field not found - trying any visible text input")
            email_field = page.wait_for_selector('input[type="text"]', timeout=10000)

        if not email_field:
            log.error("Could not find email input field")
            return False

        log.info(f"Filling email: {X_EMAIL}")
        for char in X_EMAIL:
            email_field.type(char, delay=50)
        time.sleep(2)
        page.keyboard.press("Enter")
        time.sleep(5)

        log.info("Checking for username challenge ...")
        try:
            challenge = page.wait_for_selector('input[name="username"]', timeout=8000)
            log.info(f"Filling username: {X_USERNAME}")
            for char in X_USERNAME:
                challenge.type(char, delay=50)
            time.sleep(1)
            page.keyboard.press("Enter")
            time.sleep(5)
        except:
            log.info("No username challenge detected, proceeding ...")

        log.info("Waiting for password field ...")
        try:
            pw_field = page.wait_for_selector('input[name="password"]', timeout=10000)
            log.info("Filling password...")
            for char in X_PASSWORD:
                pw_field.type(char, delay=50)
            time.sleep(2)
            page.keyboard.press("Enter")
            time.sleep(8)
        except:
            log.error("Password field not found - login failed")
            return False

        time.sleep(5)
        if _is_logged_in(page) or "/home" in page.url.lower():
            log.info("✓ Login successful")
            return True
        else:
            log.warning(f"Login verification inconclusive. URL: {page.url}")
            return True

    except Exception as e:
        log.error(f"Login error: {e}")
        return False


# ──────────────────────────────────────────────────────────
#  COMMENT SCRAPER  (top 5 replies)
# ──────────────────────────────────────────────────────────

def _scrape_comments(page, tweet_url):
    """Navigates to a single tweet and scrapes the top 5 replies from OTHER users (not @Arattai)."""
    comments = []
    try:
        log.info(f"Opening tweet detail: {tweet_url}")
        page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        page.mouse.wheel(0, 600)
        time.sleep(2)
        page.mouse.wheel(0, 800)
        time.sleep(2)
        try:
            page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
        except:
            log.warning(f"No tweets found in detail page: {tweet_url}")
            return []

        nodes = page.query_selector_all('[data-testid="tweet"]')
        log.info(f"Detail page: detected {len(nodes)} tweet nodes.")

        for node in nodes[1:]:
            if len(comments) >= 5:
                break
            try:
                body_el = node.query_selector('[data-testid="tweetText"]')
                if not body_el:
                    continue
                body = body_el.inner_text().strip()
                if not body:
                    continue

                author_display = "User"
                author_handle = ""
                name_el = node.query_selector('[data-testid="User-Name"]')
                if name_el:
                    raw = name_el.inner_text().strip()
                    lines = [l.strip() for l in raw.split("\n") if l.strip()]
                    if lines:
                        author_display = lines[0]
                    for part in lines:
                        if part.startswith("@"):
                            author_handle = part.lower()
                            break

                if author_handle in ("@arattai", "@arattaitv"):
                    log.info(f"Skipping @Arattai self-reply.")
                    continue

                if any(c["body"] == body for c in comments):
                    continue

                comments.append({"author": author_display, "body": body})
            except Exception:
                continue

        try:
            page.evaluate("window.stop()")
        except Exception:
            pass

    except Exception as e:
        log.warning(f"Comment scraping failed for {tweet_url}: {e}")

    log.info(f"Successfully captured {len(comments)} comments (non-Arattai).")
    return comments


# ──────────────────────────────────────────────────────────
#  STATS HELPER
# ──────────────────────────────────────────────────────────

def _parse_stats(node):
    stats = {"replies": "0", "reposts": "0", "likes": "0", "views": "0"}
    try:
        for testid, key in [("reply", "replies"), ("retweet", "reposts"), ("like", "likes")]:
            el = node.query_selector(f'[data-testid="{testid}"]')
            if el:
                stats[key] = el.inner_text().strip() or "0"
        view_el = node.query_selector('[data-testid="app-text-transition-container"]')
        if view_el:
            stats["views"] = view_el.inner_text().strip() or "0"
    except Exception:
        pass
    return stats


# ──────────────────────────────────────────────────────────
#  IMAGE EXTRACTION FROM TWEET NODE
# ──────────────────────────────────────────────────────────

def _extract_post_images(node):
    """Extract media image URLs from a tweet DOM node."""
    images = []
    try:
        img_els = node.query_selector_all('img[src]')
        for img in img_els:
            src = img.get_attribute('src') or ''
            if 'pbs.twimg.com/media/' not in src:
                continue
            src = re.sub(r'name=[a-z0-9]+', 'name=large', src)
            if src not in images:
                images.append(src)
    except Exception as e:
        log.warning(f'_extract_post_images error: {e}')
    return images


def _download_image(url, dest_path, cookies=None):
    """Download a single image URL to dest_path and compress it immediately."""
    try:
        req = _urlreq.Request(
            url,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                ),
                'Referer': 'https://x.com/',
            },
        )
        if cookies:
            req.add_header('Cookie', cookies)
        with _urlreq.urlopen(req, timeout=20) as resp:
            raw_data = resp.read()
        with Image.open(io.BytesIO(raw_data)) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(dest_path, format="JPEG", quality=70, optimize=True)
        return os.path.exists(dest_path) and os.path.getsize(dest_path) > 500
    except Exception as e:
        log.warning(f'Image download/compression failed {url}: {e}')
        return False


def _count_text_to_int(text):
    """Convert count text like '43.2K'/'1,234'/'1.4M' to an integer."""
    if not text:
        return 0
    s = text.strip().replace(",", "").upper()
    m = re.match(r"^(\d+(?:\.\d+)?)([KMB])?$", s)
    if not m:
        return 0
    n = float(m.group(1))
    suf = m.group(2)
    if suf == "K":
        n *= 1_000
    elif suf == "M":
        n *= 1_000_000
    elif suf == "B":
        n *= 1_000_000_000
    return int(n)


def _extract_followers(page):
    """Best-effort extraction of follower count from X profile header."""
    try:
        page.wait_for_selector('a[href*="/followers"], a[href*="/verified_followers"]', timeout=12000)
    except Exception:
        pass

    selectors = [
        'a[href$="/verified_followers"]',
        'a[href$="/followers"]',
        'a[href*="/followers"]',
    ]
    pat = re.compile(r"^\d+(?:[\.,]\d+)?(?:[KMB])?$", re.IGNORECASE)
    in_text_pat = re.compile(r"(\d+(?:[\.,]\d+)?(?:[KMB])?)", re.IGNORECASE)

    for sel in selectors:
        try:
            links = page.query_selector_all(sel)
            for link in links:
                raw_text = (link.inner_text() or "").strip()
                if not raw_text:
                    continue
                m = in_text_pat.search(raw_text.replace(" ", ""))
                if m:
                    t = m.group(1).upper()
                    if pat.match(t):
                        return t, _count_text_to_int(t)
                spans = link.query_selector_all("span")
                for sp in spans:
                    t = (sp.inner_text() or "").strip().replace(" ", "").upper()
                    if pat.match(t):
                        return t, _count_text_to_int(t)
        except Exception:
            continue

        try:
            candidates = page.evaluate(
                """() => {
                    const out = [];
                    const push = (v) => {
                        const t = String(v || '').replace(/\s+/g, ' ').trim();
                        if (t) out.push(t);
                    };
                    document.querySelectorAll('a[href*="/followers"],a[href*="/verified_followers"]').forEach(a => {
                        push(a.textContent);
                        push(a.getAttribute('aria-label'));
                    });
                    document.querySelectorAll('[aria-label*="Followers" i]').forEach(el => {
                        push(el.getAttribute('aria-label'));
                    });
                    return out;
                }"""
            )
            for c in candidates or []:
                m = in_text_pat.search(c.replace(" ", ""))
                if m:
                    t = m.group(1).upper()
                    if pat.match(t):
                        return t, _count_text_to_int(t)
        except Exception:
            pass

    try:
        body_text = page.inner_text("body")
        m = re.search(r"(\d+(?:[\.,]\d+)?(?:[KMB])?)\s+Followers", body_text, re.IGNORECASE)
        if m:
            t = m.group(1).replace(" ", "").upper()
            return t, _count_text_to_int(t)
    except Exception:
        pass

    return "", 0


def _is_stale_date(date_str, max_age_days=45):
    """Return True when tweet date is older than max_age_days."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days > max_age_days
    except Exception:
        return True


def _collect_live_search_posts(page, seen_links, limit):
    """Collect recent posts from X search as fallback when profile posts are stale."""
    posts = []
    search_queries = [
        "from:Arattai",
        "Arattai -is:retweet",
        "Arattai has:images",
        "@Arattai",
    ]
    for search_query in search_queries:
        if len(posts) >= limit:
            break
        try:
            search_url = f"https://x.com/search?q={search_query.replace(' ', '%20')}&f=live"
            log.info(f"Searching: {search_query}")
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)
            for sel in ['#layers', '[data-testid="BottomBar"]', '[data-testid="sheetDialog"]']:
                try:
                    page.evaluate(f"document.querySelector('{sel}')?.remove()")
                except:
                    pass
            for scroll_attempt in range(8):
                tweet_nodes = page.query_selector_all('[data-testid="tweet"]')
                log.info(f"Search '{search_query}' scroll {scroll_attempt + 1}: {len(tweet_nodes)} tweets visible")
                for node in tweet_nodes:
                    if len(posts) >= limit:
                        return posts
                    try:
                        time_el = node.query_selector("time")
                        if not time_el:
                            continue
                        date_str = (time_el.get_attribute("datetime") or "")[:10]
                        link_el = time_el.evaluate_handle("el => el.closest('a')")
                        href = link_el.get_attribute("href") if link_el else ""
                        tweet_url = f"https://x.com{href}" if href and href.startswith("/") else href
                        if not tweet_url or tweet_url in seen_links:
                            continue
                        body_el = node.query_selector('[data-testid="tweetText"]')
                        body = body_el.inner_text().strip() if body_el else ""
                        if not body:
                            continue
                        seen_links.add(tweet_url)
                        posts.append({
                            "node": node,
                            "url": tweet_url,
                            "date": date_str,
                            "body": body,
                            "stats": _parse_stats(node),
                            "datetime": (time_el.get_attribute("datetime") or ""),
                        })
                        log.info(f"Found: {tweet_url} ({date_str})")
                    except Exception:
                        continue
                if len(posts) >= limit:
                    return posts
                if scroll_attempt < 7:
                    page.mouse.wheel(0, 1600)
                    time.sleep(2)
            if len(posts) >= limit:
                break
        except Exception as e:
            log.warning(f"Search query '{search_query}' failed: {e}")
            continue
    log.info(f"Live search collected {len(posts)} posts")
    return posts


# ──────────────────────────────────────────────────────────
#  SESSION MANAGEMENT
# ──────────────────────────────────────────────────────────

if os.name == "nt":
    SESSION_FILE = str(_BACKEND_DIR / "x_session.json")
else:
    SESSION_FILE = "/tmp/x_session.json"


def _save_session(context):
    """Save browser cookies to disk for reuse. Persists across runs."""
    try:
        storage = context.storage_state()
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(storage, f)
        log.info(f"✓ Session saved to {SESSION_FILE}")
        return True
    except Exception as e:
        log.error(f"Failed to save session: {e}")
        return False


def _validate_session_file():
    """Check if session file exists and has valid X auth cookies."""
    candidates = [SESSION_FILE]
    if os.name != "nt":
        deploy_path = str(_BACKEND_DIR / "x_session.json")
        if deploy_path not in candidates:
            candidates.append(deploy_path)

    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
            cookies = data.get("cookies", [])
            cookie_names = {c.get("name") for c in cookies if isinstance(c, dict)}
            has_auth = "auth_token" in cookie_names
            has_ct0 = "ct0" in cookie_names
            if has_auth and has_ct0:
                log.info(f"✓ Valid X session at: {path}")
                if path != SESSION_FILE and os.name != "nt":
                    try:
                        import shutil
                        shutil.copy2(path, SESSION_FILE)
                        log.info(f"✓ Copied session to {SESSION_FILE}")
                    except Exception as ce:
                        log.warning(f"Could not copy session to /tmp: {ce}")
                return True
            else:
                log.warning(f"Session at {path} missing auth cookies. Found: {cookie_names & {'auth_token','ct0','twid'}}")
        except Exception as e:
            log.warning(f"Session file invalid at {path}: {e}")

    log.warning(f"No valid X session found. Checked: {candidates}")
    return False


def _is_logged_in(page):
    """Check if the current page shows a logged-in X state."""
    try:
        return bool(page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]'))
    except Exception:
        return False


# ──────────────────────────────────────────────────────────
#  MAIN SCRAPER
# ──────────────────────────────────────────────────────────

def fetch_twitter_data():
    if not _PW_AVAIL:
        log.error("playwright not installed.")
        return _empty_twitter()

    raw_posts        = []
    screenshot_paths = []
    followers_text   = ""
    followers_count  = 0

    with sync_playwright() as pw:
        _resolved_session = _get_session_path() if os.name != "nt" else SESSION_FILE
        session_kwargs = {}
        _session_to_use = _resolved_session if _resolved_session and os.path.exists(_resolved_session) else None
        if _session_to_use:
            log.info(f"Found session file at: {_session_to_use}")
            session_kwargs["storage_state"] = _session_to_use
        else:
            log.warning("No session file found — will attempt fresh login")

        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--memory-pressure-off",
                "--js-flags=--max-old-space-size=256",
                "--single-process",
                "--disable-extensions",
                "--disable-component-update",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1024, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Kolkata",
            **session_kwargs,
        )
        context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

        page = context.new_page()
        log.info(f"Navigating to {X_PROFILE} to check session ...")
        page.goto(X_PROFILE, wait_until="domcontentloaded", timeout=40000)
        time.sleep(5)

        if _is_logged_in(page):
            log.info("Session valid — skipping login ✓")
        else:
            log.info("Session expired or missing — logging in fresh ...")
            logged_in = _login(page)
            if logged_in:
                _save_session(context)
            log.info(f"Navigating to {X_PROFILE} ...")
            page.goto(X_PROFILE, wait_until="domcontentloaded", timeout=40000)
            time.sleep(5)

        followers_text, followers_count = _extract_followers(page)
        if followers_text:
            log.info(f"Followers scraped: {followers_text} ({followers_count})")
        else:
            log.warning("Could not scrape follower count from profile header")

        overlay_selectors = [
            '#layers',
            '[data-testid="BottomBar"]',
            '[data-testid="sheetDialog"]',
            'div[role="group"] > div > div > div > div > [role="button"]',
            '.r-12vffkv',
        ]
        for sel in overlay_selectors:
            try:
                page.evaluate(f"document.querySelectorAll('{sel}').forEach(el => el.remove())")
            except Exception:
                pass

        try:
            for text in ["Not now", "Refuse optional cookies", "Close"]:
                btn = page.get_by_role("button", name=text).first
                if btn.is_visible():
                    btn.click()
                    log.info(f"Dismissed overlay button: {text}")
        except Exception:
            pass

        try:
            page.wait_for_selector('[data-testid="tweet"]', timeout=20000)
        except Exception:
            log.error("No tweets found on profile page.")
            browser.close()
            return _empty_twitter()

        page.mouse.wheel(0, 600)
        time.sleep(2)

        seen_links = set()
        originals = []
        reposts = []

        for attempt in range(6):
            tweet_nodes = page.query_selector_all('[data-testid="tweet"]')
            log.info(f"Scan {attempt + 1}: found {len(tweet_nodes)} tweet elements on profile.")

            for node in tweet_nodes:
                try:
                    social_ctx = node.query_selector('[data-testid="socialContext"]')
                    social_text = social_ctx.inner_text().lower() if social_ctx else ""
                    is_repost = "repost" in social_text
                    is_pinned = "pinned" in social_text

                    date_str = ""
                    datetime_val = ""
                    time_el = node.query_selector("time")
                    if time_el:
                        datetime_val = time_el.get_attribute("datetime") or ""
                        date_str = datetime_val[:10]
                    else:
                        spans = node.query_selector_all("span")
                        for s in spans:
                            txt = s.inner_text().strip().lower()
                            if re.match(r'^(\d+[smh]|now|just now)$', txt):
                                date_str = datetime.now().strftime("%Y-%m-%d")
                                datetime_val = datetime.now().isoformat()
                                break
                            if re.match(r'^[a-z]{3}\s\d{1,2}$', txt):
                                date_str = f"2026-{txt}"
                                break

                    tweet_url = ""
                    link_el = node.query_selector('a[href*="/status/"]')
                    if link_el:
                        href = link_el.get_attribute("href")
                        if href:
                            tweet_url = f"https://x.com{href}" if href.startswith("/") else href

                    if not tweet_url or tweet_url in seen_links:
                        continue
                    seen_links.add(tweet_url)

                    body_el = node.query_selector('[data-testid="tweetText"]')
                    body = body_el.inner_text().strip() if body_el else ""
                    if not body:
                        img_check = node.query_selector('img[src*="pbs.twimg.com/media/"]')
                        if not img_check:
                            continue
                        body = "[Image Post]"

                    stats = _parse_stats(node)

                    candidate = {
                        "node": node,
                        "url": tweet_url,
                        "date": date_str,
                        "body": body,
                        "stats": stats,
                        "datetime": datetime_val,
                        "is_pinned": is_pinned,
                    }
                    log.info(f"Found tweet: {tweet_url} | Date: {date_str}")
                    if is_repost:
                        reposts.append(candidate)
                    else:
                        originals.append(candidate)
                except Exception as e:
                    log.warning(f"Tweet node error: {e}")

            if len(originals) >= 5:
                break
            if (len(originals) + len(reposts)) >= 12:
                break

            page.mouse.wheel(0, 1600)
            time.sleep(2)

        originals = sorted(originals, key=lambda x: (x.get("is_pinned", False), x.get("datetime", "")), reverse=True)
        reposts = sorted(reposts, key=lambda x: (x.get("is_pinned", False), x.get("datetime", "")), reverse=True)

        selected = originals[:5]
        if len(selected) < 5:
            need = 5 - len(selected)
            selected.extend(reposts[:need])

        max_age = 14 if not _is_logged_in(page) else 45
        if selected and _is_stale_date(selected[0].get("date", ""), max_age_days=max_age):
            backup_selected = list(selected)
            log.info(
                f"Latest @Arattai post is stale ({selected[0].get('date', '')}) - max_age_days={max_age}. Trying live search ..."
            )
            selected = []
            selected.extend(_collect_live_search_posts(page, seen_links, 5))
            if len(selected) < 5:
                need = 5 - len(selected)
                if backup_selected:
                    log.info(f"Live search returned {len(selected)} posts, filling remaining {need} from timeline")
                    selected.extend(backup_selected[:need])
                else:
                    log.warning("No posts available from timeline or live search!")

        log.info(
            f"Recent post selection: originals={len(originals)}, reposts={len(reposts)}, selected={len(selected)}"
        )

        count = 0
        for cand in selected:
            shot_path = os.path.join(DATA_DIR, f"tweet_{count}.png")
            try:
                node = cand.get("node")
                captured = False
                if node:
                    try:
                        node.scroll_into_view_if_needed(timeout=5000)
                        time.sleep(1)
                        node.screenshot(path=shot_path, type="jpeg", quality=70)
                        captured = os.path.exists(shot_path)
                    except Exception as e:
                        log.warning(f"Timeline node screenshot failed for post {count}: {e}")

                if not captured:
                    try:
                        page.goto(cand["url"], wait_until="commit", timeout=30000)
                        page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
                        page.screenshot(path=shot_path, type="jpeg", quality=70, full_page=False)
                        captured = os.path.exists(shot_path)
                    except Exception:
                        pass

                screenshot_paths.append(shot_path if os.path.exists(shot_path) else "")
            except Exception as e:
                log.warning(f"Screenshot {count} failed: {e}")
                screenshot_paths.append("")

            post_image_urls = []
            post_image_inline = {}
            node_for_images = cand.get("node")
            if node_for_images:
                raw_img_urls = _extract_post_images(node_for_images)
                log.info(f"Post {count}: found {len(raw_img_urls)} media image(s).")
                try:
                    cookie_str = "; ".join(
                        f"{c['name']}={c['value']}"
                        for c in context.cookies()
                        if c.get('domain', '').endswith('twimg.com')
                           or c.get('domain', '').endswith('twitter.com')
                           or c.get('domain', '').endswith('x.com')
                    )
                except Exception:
                    cookie_str = None
                for img_idx, img_url in enumerate(raw_img_urls):
                    img_filename = f"tweet_{count}_img{img_idx}.jpg"
                    img_path = os.path.join(DATA_DIR, img_filename)
                    ok = _download_image(img_url, img_path, cookies=cookie_str)
                    if ok:
                        inline_url = _file_to_data_url(img_path)
                        if inline_url:
                            post_image_inline[img_filename] = inline_url
                            post_image_urls.append(_local_file_url(img_path))
                            log.info(f"  ✓ Saved + inlined image {img_idx}: {img_filename}")
                        else:
                            post_image_urls.append(_local_file_url(img_path))
                            log.info(f"  ✓ Saved image {img_idx}: {img_filename}")
                    else:
                        log.warning(f"  ✗ Could not download image {img_idx}: {img_url}")

            raw_posts.append({
                "url":                cand["url"],
                "date":               cand["date"],
                "datetime":           cand.get("datetime", ""),
                "body":               cand["body"],
                "stats":              cand["stats"],
                "post_images":        post_image_urls,
                "post_images_inline": post_image_inline,
            })
            log.info(f"Post {count}: {cand['url']} ({cand['date']})")
            count += 1

        # Scrape comments
        for i, post in enumerate(raw_posts):
            log.info(f"Scraping comments for post {i} ...")
            try:
                temp_page = context.new_page()
                post["comments"] = _scrape_comments(temp_page, post["url"])
                temp_page.close()
            except Exception as ce:
                log.warning(f"Comment scrape error post {i}: {ce}")
                post["comments"] = []
            time.sleep(1)

        browser.close()

    # Upload to Catalyst
    valid_paths   = [p for p in screenshot_paths if p and os.path.exists(p)]
    log.info(f"Uploading {len(valid_paths)} screenshots to Catalyst ...")
    uploaded_urls = _catalyst_upload(valid_paths)

    url_iter = iter(uploaded_urls)
    inline_screenshots = {}
    for i, post in enumerate(raw_posts):
        has_shot = (
            i < len(screenshot_paths)
            and screenshot_paths[i]
            and os.path.exists(screenshot_paths[i])
        )
        if not has_shot:
            post["screenshot_url"] = ""
            continue

        shot_name = os.path.basename(screenshot_paths[i])
        inline_url = _file_to_data_url(screenshot_paths[i])
        if inline_url and shot_name:
            inline_screenshots[shot_name] = inline_url

        for img_name, img_data_url in (post.get("post_images_inline") or {}).items():
            inline_screenshots[img_name] = img_data_url

        shot_url = next(url_iter, "")
        if not shot_url:
            shot_url = _local_file_url(screenshot_paths[i])
        post["screenshot_url"] = shot_url

    log.info(f"Done – {len(raw_posts)} posts scraped fresh.")
    return {
        "fetched_at":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":           X_PROFILE,
        "followers":         followers_text,
        "followers_count":   followers_count,
        "recent_posts":      raw_posts,
        "inline_screenshots": inline_screenshots,
    }


def _empty_twitter():
    return {
        "fetched_at":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":           X_PROFILE,
        "followers":         "",
        "followers_count":   0,
        "recent_posts":      [],
        "inline_screenshots": {},
    }


# ──────────────────────────────────────────────────────────
#  INCREMENTAL MERGE: new posts + old posts → top 5
# ──────────────────────────────────────────────────────────

def _merge_posts(new_posts, prev_posts, prev_inline_screenshots, max_posts=5):
    """
    Merge freshly scraped posts with previously saved posts.

    Rules:
      1. Dedup by URL (tweet permalink).
      2. New posts take priority over old ones for all fields
         EXCEPT screenshot_url and inline images — if a new scrape
         failed to produce a screenshot for a URL that already had one,
         the old screenshot is carried over.
      3. Sort by datetime descending (newest first).
      4. Keep top max_posts.
      5. Rebuild inline_screenshots map to only contain entries for
         posts that made it into the final top-5 (prevents unbounded growth).

    Returns: (merged_posts, merged_inline_screenshots)
    """
    # Index previous posts by URL for O(1) lookup
    prev_by_url = {p["url"]: p for p in prev_posts if p.get("url")}

    # Build merged dict: URL → post data (new post wins on body/stats/comments)
    merged_by_url = {}

    # Start with ALL new posts
    for p in new_posts:
        url = p.get("url", "")
        if not url:
            continue
        entry = dict(p)
        # If this URL existed before and new scrape has no screenshot, carry old one
        if not entry.get("screenshot_url") and url in prev_by_url:
            old = prev_by_url[url]
            old_shot = old.get("screenshot_url", "")
            if old_shot:
                entry["screenshot_url"] = old_shot
                log.info(f"Carried over screenshot for existing URL: {url}")
        # If new scrape has no comments but old has some, carry old comments
        if not entry.get("comments") and url in prev_by_url:
            old_comments = prev_by_url[url].get("comments", [])
            if old_comments:
                entry["comments"] = old_comments
                log.info(f"Carried over {len(old_comments)} comments for: {url}")
        merged_by_url[url] = entry

    # Add OLD posts that are NOT in new scrape (they will sit behind new ones)
    for p in prev_posts:
        url = p.get("url", "")
        if not url or url in merged_by_url:
            continue
        entry = dict(p)
        # Repair stale /api/data/ screenshot URLs for old posts
        shot = entry.get("screenshot_url", "")
        if shot.startswith("/api/data/"):
            # Keep it — server.py will serve it from inline_screenshots
            pass
        merged_by_url[url] = entry

    # Sort: newest datetime first (empty datetime goes last)
    all_posts = list(merged_by_url.values())
    all_posts.sort(key=lambda x: x.get("datetime", ""), reverse=True)

    # Keep top max_posts
    top_posts = all_posts[:max_posts]

    log.info(
        f"Merge result: {len(new_posts)} new + {len(prev_posts)} prev "
        f"→ {len(all_posts)} unique → top {len(top_posts)} kept"
    )

    # Rebuild inline_screenshots: only keep entries for posts in top_posts
    surviving_urls = {p["url"] for p in top_posts if p.get("url")}
    new_inline = {}

    # Carry over OLD inline screenshots for surviving posts
    for p in top_posts:
        url = p.get("url", "")
        if url in prev_by_url:
            old = prev_by_url[url]
            old_inline_map = old.get("post_images_inline", {})
            for fname, data_url in old_inline_map.items():
                if fname not in new_inline:
                    new_inline[fname] = data_url
            # Also carry screenshot inline from prev_inline_screenshots
            shot = old.get("screenshot_url", "")
            if shot.startswith("/api/data/"):
                shot_fname = shot.replace("/api/data/", "")
                if shot_fname in prev_inline_screenshots and shot_fname not in new_inline:
                    new_inline[shot_fname] = prev_inline_screenshots[shot_fname]

    # Add NEW inline screenshots (override old if same filename, which is fine)
    for p in new_posts:
        url = p.get("url", "")
        if url not in surviving_urls:
            continue
        for fname, data_url in (p.get("post_images_inline") or {}).items():
            new_inline[fname] = data_url
        # screenshot inline is already in the new_inline_screenshots from fetch_twitter_data

    return top_posts, new_inline


# ──────────────────────────────────────────────────────────
#  DATA.JSON INTEGRATION
# ──────────────────────────────────────────────────────────

def run_twitter_cycle():
    log.info("=== Starting Twitter Fetch Cycle ===")
    twitter_data = fetch_twitter_data()

    # ── LLM enrichment: add timing to all X comments ──────
    if _ENRICH_AVAIL and twitter_data.get("recent_posts"):
        log.info("Enriching X comment timing via Qwen LLM...")
        try:
            twitter_data["recent_posts"] = enrich_twitter_comments(twitter_data["recent_posts"])
            log.info("✓ X comment timing enrichment complete.")
        except Exception as enrich_err:
            log.error(f"X comment enrichment failed (non-fatal): {enrich_err}")
    else:
        if not _ENRICH_AVAIL:
            log.warning("enrich_reviews not available — X comments will have no timing.")

    def _read_json_safe(path):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    obj = json.load(fh)
                    return obj if isinstance(obj, dict) else {}
        except Exception:
            pass
        return {}

    # Read current data.json (from /tmp on Linux, backend dir on Windows)
    data = _read_json_safe(DATA_FILE)

    # Fallback: pull from backend dir or public dir if /tmp is empty
    fallback_backend = _read_json_safe(str(_BACKEND_DIR / "data.json"))
    fallback_public  = _read_json_safe(str(_BACKEND_DIR.parent / "public" / "data.json"))
    for k, v in fallback_backend.items():
        data.setdefault(k, v)
    for k, v in fallback_public.items():
        data.setdefault(k, v)

    # Previous twitter state
    prev_twitter          = data.get("twitter", {}) if isinstance(data, dict) else {}
    prev_posts            = prev_twitter.get("recent_posts", []) if isinstance(prev_twitter, dict) else []
    prev_inline_shots     = prev_twitter.get("inline_screenshots", {}) if isinstance(prev_twitter, dict) else {}

    new_posts    = twitter_data.get("recent_posts", [])
    new_inline   = twitter_data.get("inline_screenshots", {})

    if new_posts:
        # ── INCREMENTAL MERGE ──────────────────────────────────────────────────
        # Combine new_inline from the fresh scrape with prev_inline_shots so
        # _merge_posts can carry forward old screenshot data for surviving posts.
        combined_inline_prev = {**prev_inline_shots, **new_inline}
        merged_posts, merged_inline = _merge_posts(
            new_posts, prev_posts, combined_inline_prev, max_posts=5
        )

        twitter_data["recent_posts"]      = merged_posts
        twitter_data["inline_screenshots"] = merged_inline

        # Preserve follower count if new scrape missed it
        if not twitter_data.get("followers") and prev_twitter.get("followers"):
            twitter_data["followers"]       = prev_twitter.get("followers", "")
        if not twitter_data.get("followers_count") and prev_twitter.get("followers_count"):
            twitter_data["followers_count"] = prev_twitter.get("followers_count", 0)

    else:
        # ── ZERO POSTS RETURNED: keep old data entirely ────────────────────────
        log.warning("Twitter scrape returned 0 posts; preserving previous X data.")
        # For old /api/data/ screenshot URLs: they're still served from inline_screenshots
        twitter_data["recent_posts"]      = prev_posts
        twitter_data["inline_screenshots"] = prev_inline_shots
        if not twitter_data.get("followers") and prev_twitter.get("followers"):
            twitter_data["followers"]       = prev_twitter.get("followers", "")
        if not twitter_data.get("followers_count") and prev_twitter.get("followers_count"):
            twitter_data["followers_count"] = prev_twitter.get("followers_count", 0)

    data["twitter"] = twitter_data

    # ── Write data.json ─────────────────────────────────────────────────────────
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        log.info(f"data.json updated – {len(twitter_data['recent_posts'])} posts saved.")
    except Exception as e:
        log.error(f"Write failed to {DATA_FILE}: {e}")

    # ── Also write to backend/data.json for persistence across Railway restarts ──
    # Railway may wipe /tmp but the image layer (backend dir) persists between deploys.
    backend_data_file = str(_BACKEND_DIR / "data.json")
    try:
        with open(backend_data_file, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        log.info(f"Backup data.json written to {backend_data_file}")
    except Exception as e:
        log.warning(f"Could not write backup data.json: {e}")

    # ── Sync to public/data.json for Vite dev server ───────────────────────────
    public_data = _BACKEND_DIR.parent / "public" / "data.json"
    try:
        public_data.parent.mkdir(parents=True, exist_ok=True)
        with open(public_data, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass

    log.info("=== Twitter Cycle Complete ===")
    log.info(
        f"    Posts in data.json: {[p.get('url','?')[-40:] for p in twitter_data['recent_posts']]}"
    )


# ──────────────────────────────────────────────────────────
#  STANDALONE
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Standalone – fetching once then every 15 minutes.")
    while True:
        run_twitter_cycle()
        log.info("Sleeping 15 minutes ...")
        time.sleep(15 * 60)

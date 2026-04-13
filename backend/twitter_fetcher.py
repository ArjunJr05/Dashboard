"""
twitter_fetcher.py
==================
Logs into X (Twitter) with provided credentials, navigates to @Arattai,
captures screenshots of the 5 most recent posts, scrapes top 5 comments
per post, uploads everything to Zoho Catalyst File Store (deleting stale
files first), then writes the result into data.json.

Schedule: called every 15 minutes from server.py
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
    # Try to install playwright if it's missing
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
            
            # --- Auto-cleaning for Chrome Extension exports ---
            if isinstance(data, dict) and "cookies" in data:
                cookies = data["cookies"]
                for c in cookies:
                    # 1. Fix expiration key
                    if "expirationDate" in c:
                        c["expires"] = c.pop("expirationDate")
                    
                    # 2. Fix sameSite values (Playwright only allows Strict, Lax, or None)
                    ss = str(c.get("sameSite", "")).lower()
                    if ss in ["lax", "strict", "none"]:
                        c["sameSite"] = ss.capitalize()
                    else:
                        c["sameSite"] = "None" # Default fallback
                
                # Wrap it back in the format Playwright expects
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
    """Inline image bytes as a data URL. Auto-detects mime type from extension."""
    try:
        ext = os.path.splitext(path)[1].lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
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
    # Always keep a local URL fallback so frontend can render screenshots in dev.
    local_urls = [_local_file_url(p) for p in file_paths]
    prod_fallback_urls = ["" for _ in file_paths]

    if not _CATALYST_AVAIL:
        if os.name == "nt":
            log.warning("zcatalyst-sdk not available – using local screenshot URLs for dev.")
            return local_urls
        log.warning("zcatalyst-sdk not available in production – using inline screenshot fallback.")
        return prod_fallback_urls

    # Enable upload by default in production (Linux/AppSail), keep it opt-in for local dev.
    default_upload = "1" if os.name != "nt" else "0"
    if os.environ.get("ENABLE_CATALYST_UPLOAD", default_upload) != "1":
        if os.name == "nt":
            log.info("Catalyst upload disabled via ENABLE_CATALYST_UPLOAD. Using local screenshot URLs for dev.")
            return local_urls
        log.info("Catalyst upload disabled in production. Using inline screenshot fallback.")
        return prod_fallback_urls

    urls = []

    try:
        # Check if environment is initialized
        sdk_app = zcatalyst_sdk.initialize()
        fs      = sdk_app.filestore()
        folder  = fs.folder(CATALYST_FOLDER_ID)

        # 1. Delete old screenshots
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

        # 2. Upload new screenshots
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
#  X LOGIN  (domcontentloaded — avoids networkidle timeout)
# ──────────────────────────────────────────────────────────

def _login(page):
    """Robust X login with fallback to guest view."""
    try:
        log.info("Navigating to X login flow ...")
        page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)

        log.info("Attempting standard email/password login ...")
        
        # Try multiple selectors for email input field
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
        
        # Type email slowly to avoid bot detection
        log.info(f"Filling email: {X_EMAIL}")
        for char in X_EMAIL:
            email_field.type(char, delay=50)
        time.sleep(2)
        page.keyboard.press("Enter")
        time.sleep(5)

        # Handle username challenge (if needed)
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

        # Look for password field
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

        # Verify login success
        time.sleep(5)
        if _is_logged_in(page) or "/home" in page.url.lower():
            log.info("✓ Login successful")
            return True
        else:
            log.warning(f"Login verification inconclusive. URL: {page.url}")
            return True  # Proceed anyway - session might work

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
        # Navigate with shorter timeout and no waiting for images to save memory
        page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        # Scroll slightly to trigger reply loading
        page.mouse.wheel(0, 600)
        time.sleep(2)
        page.mouse.wheel(0, 800)
        time.sleep(2)

        # Wait for reply nodes
        try:
            page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
        except:
            log.warning(f"No tweets found in detail page: {tweet_url}")
            return []

        nodes = page.query_selector_all('[data-testid="tweet"]')
        log.info(f"Detail page: detected {len(nodes)} tweet nodes.")

        # Skip index 0 (main post). Start from 1 for replies.
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

                # Extract author display name AND @handle
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

        # Free memory: navigate away before returning
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
    """
    Extract media image URLs from a tweet DOM node.
    Returns a list of high-resolution pbs.twimg.com image URLs found
    in <img> elements inside the tweet card (excludes avatars/icons).
    """
    images = []
    try:
        # All img tags inside the tweet node
        img_els = node.query_selector_all('img[src]')
        for img in img_els:
            src = img.get_attribute('src') or ''
            # Only keep tweet media images (pbs.twimg.com), skip avatars/emoji
            if 'pbs.twimg.com/media/' not in src:
                continue
            # Upgrade to highest quality: replace format param and request 'large'
            # e.g. https://pbs.twimg.com/media/XYZ?format=jpg&name=small  →  name=large
            src = re.sub(r'name=[a-z0-9]+', 'name=large', src)
            if src not in images:
                images.append(src)
    except Exception as e:
        log.warning(f'_extract_post_images error: {e}')
    return images


def _download_image(url, dest_path, cookies=None):
    """
    Download a single image URL to dest_path.
    Uses a browser-like User-Agent; passes optional cookie header.
    Returns True on success.
    """
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
            with open(dest_path, 'wb') as fh:
                fh.write(resp.read())
        return os.path.exists(dest_path) and os.path.getsize(dest_path) > 500
    except Exception as e:
        log.warning(f'Image download failed {url}: {e}')
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

                # Try full link text first (e.g. "43.2K Followers")
                m = in_text_pat.search(raw_text.replace(" ", ""))
                if m:
                    t = m.group(1).upper()
                    if pat.match(t):
                        return t, _count_text_to_int(t)

                # Fallback: inspect nested spans
                spans = link.query_selector_all("span")
                for sp in spans:
                    t = (sp.inner_text() or "").strip().replace(" ", "").upper()
                    if pat.match(t):
                        return t, _count_text_to_int(t)
        except Exception:
            continue

        # Deep fallback: collect visible candidate texts from DOM and parse count-like token.
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
    
    # Try multiple search queries in order of preference
    search_queries = [
        "from:Arattai",  # Posts directly from account
        "Arattai -is:retweet",  # Mentions without retweets
        "Arattai has:images",  # Posts with images
        "@Arattai",  # At mentions
    ]
    
    for search_query in search_queries:
        if len(posts) >= limit:
            break
        
        try:
            search_url = f"https://x.com/search?q={search_query.replace(' ', '%20')}&f=live"
            log.info(f"Searching: {search_query}")
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)

            # Close overlays
            for sel in ['#layers', '[data-testid="BottomBar"]', '[data-testid="sheetDialog"]']:
                try:
                    page.evaluate(f"document.querySelector('{sel}')?.remove()")
                except:
                    pass

            # Scroll and collect posts
            for scroll_attempt in range(8):  # Increased from 6
                tweet_nodes = page.query_selector_all('[data-testid="tweet"]')
                found_new = False
                
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
                        found_new = True
                        log.info(f"Found: {tweet_url} ({date_str})")
                        
                    except Exception as e:
                        continue
                
                if len(posts) >= limit:
                    return posts
                
                # Only scroll if we're finding new posts
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
#  MAIN SCRAPER
# ──────────────────────────────────────────────────────────

# Use absolute path for session file so it persists across runs and deployments
# On Linux/Catalyst: check /tmp first (written by main.py), fall back to deploy dir
# On Windows dev: use the backend directory directly
if os.name == "nt":
    SESSION_FILE = str(_BACKEND_DIR / "x_session.json")
else:
    # _get_session_path() handles: env var X_SESSION_JSON → /tmp → backend dir
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
    # On Linux, also check deploy directory as fallback if /tmp not populated yet
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
                # If found in deploy dir but not /tmp, copy it there now
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


def fetch_twitter_data():
    if not _PW_AVAIL:
        log.error("playwright not installed.")
        return _empty_twitter()

    raw_posts        = []
    screenshot_paths = []
    followers_text   = ""
    followers_count  = 0

    with sync_playwright() as pw:
        # Resolve session path (checks X_SESSION_JSON env var, then /tmp, then backend dir)
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
                "--single-process", # Crucial for 512MB RAM
            ],
        )
        # Use a smaller viewport to save RAM
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

        # Try going directly to profile — if session is valid, login is skipped
        log.info(f"Navigating to {X_PROFILE} to check session ...")
        page.goto(X_PROFILE, wait_until="domcontentloaded", timeout=40000)
        time.sleep(5)

        if _is_logged_in(page):
            log.info("Session valid — skipping login ✓")
        else:
            log.info("Session expired or missing — logging in fresh ...")
            logged_in = _login(page)
            if logged_in:
                _save_session(context)  # Save for next run
            # Navigate to profile after login
            log.info(f"Navigating to {X_PROFILE} ...")
            page.goto(X_PROFILE, wait_until="domcontentloaded", timeout=40000)
            time.sleep(5)

        # Extract profile follower count for overview dashboard
        followers_text, followers_count = _extract_followers(page)
        if followers_text:
            log.info(f"Followers scraped: {followers_text} ({followers_count})")
        else:
            log.warning("Could not scrape follower count from profile header")


        # Remove login walls / overlays
        for sel in ['#layers', '[data-testid="BottomBar"]', '[data-testid="sheetDialog"]']:
            try:
                page.evaluate(f"document.querySelector('{sel}')?.remove()")
            except Exception:
                pass

        try:
            page.wait_for_selector('[data-testid="tweet"]', timeout=20000)
        except Exception:
            log.error("No tweets found on profile page.")
            browser.close()
            return _empty_twitter()

        # Scroll a little to load more tweets past any pinned post
        page.mouse.wheel(0, 600)
        time.sleep(2)

        seen_links = set()
        count = 0
        originals = []
        reposts = []

        # Collect enough tweets by incremental scrolling.
        for attempt in range(6):
            tweet_nodes = page.query_selector_all('[data-testid="tweet"]')
            log.info(f"Scan {attempt + 1}: found {len(tweet_nodes)} tweet elements on profile.")

            for node in tweet_nodes:
                try:
                    # Read context label for filtering pinned/reposted rows.
                    social_ctx = node.query_selector('[data-testid="socialContext"]')
                    social_text = social_ctx.inner_text().lower() if social_ctx else ""
                    is_repost = "repost" in social_text
                    if "pinned" in social_text:
                        continue

                    time_el = node.query_selector("time")
                    date_str = ""
                    tweet_url = ""

                    if time_el:
                        date_str = (time_el.get_attribute("datetime") or "")[:10]
                        link_el = time_el.evaluate_handle("el => el.closest('a')")
                        if link_el:
                            href = link_el.get_attribute("href")
                            if href:
                                tweet_url = f"https://x.com{href}" if href.startswith("/") else href

                    if not tweet_url or tweet_url in seen_links:
                        continue
                    seen_links.add(tweet_url)

                    body_el = node.query_selector('[data-testid="tweetText"]')
                    body = body_el.inner_text().strip() if body_el else ""
                    stats = _parse_stats(node)

                    candidate = {
                        "node": node,
                        "url": tweet_url,
                        "date": date_str,
                        "body": body,
                        "stats": stats,
                        "datetime": (time_el.get_attribute("datetime") or "") if time_el else "",
                    }

                    if is_repost:
                        reposts.append(candidate)
                    else:
                        originals.append(candidate)
                except Exception as e:
                    log.warning(f"Tweet node error: {e}")

            if len(originals) >= 5:
                break

            # If originals are fewer, keep scrolling and allow repost fallback.
            if (len(originals) + len(reposts)) >= 12:
                break

            page.mouse.wheel(0, 1600)
            time.sleep(2)

        originals = sorted(originals, key=lambda x: x.get("datetime", ""), reverse=True)
        reposts = sorted(reposts, key=lambda x: x.get("datetime", ""), reverse=True)

        # Limit to 3 tweets to avoid OOM on 512MB RAM
        selected = originals[:3]
        if len(selected) < 3:
            need = 3 - len(selected)
            selected.extend(reposts[:need])

        # If account timeline appears stale, fill with recent live mentions.
        # More aggressive when not logged in - any post older than 14 days triggers fallback
        max_age = 14 if not _is_logged_in(page) else 45
        if selected and _is_stale_date(selected[0].get("date", ""), max_age_days=max_age):
            backup_selected = list(selected)
            log.info(
                f"Latest @Arattai post is stale ({selected[0].get('date', '')}) - max_age_days={max_age}. Trying live search ..."
            )
            selected = []
            selected.extend(_collect_live_search_posts(page, seen_links, 5))

            # If live search is blocked/empty, keep account timeline posts rather than blank feed.
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

        for cand in selected:
            # Screenshot
            shot_path = os.path.join(DATA_DIR, f"tweet_{count}.png")
            try:
                # Primary strategy: capture directly from the profile timeline node
                # (avoids login walls/rate limits that can appear on detail pages).
                node = cand.get("node")
                captured = False
                if node:
                    try:
                        node.scroll_into_view_if_needed(timeout=5000)
                    except Exception:
                        pass
                    time.sleep(0.8)
                    try:
                        node.screenshot(path=shot_path)
                        captured = os.path.exists(shot_path)
                    except Exception as e:
                        log.warning(f"Timeline node screenshot failed for post {count}: {e}")

                # Fallback strategy: open tweet detail and capture first tweet block.
                if not captured:
                    page.goto(cand["url"], wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
                    tweet_nodes = page.query_selector_all('[data-testid="tweet"]')
                    if tweet_nodes:
                        tweet_nodes[0].screenshot(path=shot_path)
                    else:
                        page.screenshot(path=shot_path, full_page=False)

                screenshot_paths.append(shot_path if os.path.exists(shot_path) else "")
                
                # UPLOAD TO CATALYST FILE STORE (Persistent Storage)
                if os.path.exists(shot_path):
                    try:
                        from zcatalyst_sdk import catalyst
                        import traceback
                        # Diagnostic: check if catalyst is already initialized
                        try:
                            cat_app = catalyst.initialize()
                        except:
                            # If it fails, it usually needs credentials on Render
                            cat_app = None

                        if cat_app:
                            filestore = cat_app.file_store()
                            folder = filestore.folder("28618000000101001")
                            log.info(f"[catalyst] Attempting upload: {shot_path}")
                            # Overwrite logic
                            result = folder.upload_file(shot_path)
                            log.info(f"✓ Screenshot {count} stored in Catalyst Cloud! ID: {result.id}")
                        else:
                            log.error("[catalyst] SDK Init Failed — NO CREDENTIALS FOUND. Please set CATALYST_PROJECT_ID and CATALYST_PROJECT_KEY in Render Env Vars.")
                    except Exception:
                        log.error(f"[catalyst] Upload failed for {shot_path}:")
                        log.error(traceback.format_exc())
            except Exception as e:
                log.warning(f"Screenshot {count} failed: {e}")
                screenshot_paths.append("")

            # ── Extract and download images from the tweet node ──────────
            post_image_urls = []
            post_image_inline = {}  # filename -> data URL (base64) for persistence
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
                        # Inline as base64 data URL so it survives /tmp resets
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
                "body":               cand["body"],
                "stats":              cand["stats"],
                "post_images":        post_image_urls,
                "post_images_inline": post_image_inline,
            })
            log.info(f"Post {count}: {cand['url']} ({cand['date']})")
            count += 1

        # Scrape comments — recreate page if it crashes mid-way
        for i, post in enumerate(raw_posts):
            log.info(f"Scraping comments for post {i} ...")
            try:
                if page.is_closed():
                    log.warning("Page was closed — reopening for comments")
                    page = context.new_page()
                post["comments"] = _scrape_comments(page, post["url"])
            except Exception as ce:
                log.warning(f"Comment scrape error post {i}: {ce}")
                try:
                    page = context.new_page()
                except Exception:
                    pass
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

        # Keep a data-url copy so server.py can serve /api/data/tweet_X.png even if local file is absent.
        shot_name = os.path.basename(screenshot_paths[i])
        inline_url = _file_to_data_url(screenshot_paths[i])
        if inline_url and shot_name:
            inline_screenshots[shot_name] = inline_url

        # Also merge this post's post_images_inline into the global map
        for img_name, img_data_url in (post.get("post_images_inline") or {}).items():
            inline_screenshots[img_name] = img_data_url

        shot_url = next(url_iter, "")
        if not shot_url:
            shot_url = _local_file_url(screenshot_paths[i])
        if shot_url.startswith("/api/data/"):
            # Serve via backend's inline screenshot route instead of thum.io (avoids X login wall)
            pass  # keep /api/data/ path — server.py will serve inline base64 from data.json
        post["screenshot_url"] = shot_url

    log.info(f"Done – {len(raw_posts)} posts.")
    return {
        "fetched_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":      X_PROFILE,
        "followers":    followers_text,
        "followers_count": followers_count,
        "recent_posts": raw_posts,
        "inline_screenshots": inline_screenshots,
    }


def _empty_twitter():
    return {
        "fetched_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":      X_PROFILE,
        "followers":    "",
        "followers_count": 0,
        "recent_posts": [],
    }


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

    data = _read_json_safe(DATA_FILE)
    # Fallback sources can contain the full dashboard payload in case /tmp is partial.
    fallback_backend = _read_json_safe(str(_BACKEND_DIR / "data.json"))
    fallback_public = _read_json_safe(str(_BACKEND_DIR.parent / "public" / "data.json"))
    for k, v in fallback_backend.items():
        data.setdefault(k, v)
    for k, v in fallback_public.items():
        data.setdefault(k, v)

    # If the current scrape fails to return posts, keep last known good X data.
    prev_twitter = data.get("twitter", {}) if isinstance(data, dict) else {}
    prev_posts = prev_twitter.get("recent_posts", []) if isinstance(prev_twitter, dict) else []
    if not twitter_data.get("recent_posts") and prev_posts:
        log.warning("Twitter scrape returned 0 posts; preserving previous X posts/screenshots.")
        repaired_posts = []
        for p in prev_posts:
            post_copy = dict(p)
            if str(post_copy.get("screenshot_url", "")).startswith("/api/data/"):
                post_copy["screenshot_url"] = _remote_tweet_screenshot(post_copy.get("url", ""))
            repaired_posts.append(post_copy)
        twitter_data["recent_posts"] = repaired_posts
        if not twitter_data.get("followers") and prev_twitter.get("followers"):
            twitter_data["followers"] = prev_twitter.get("followers", "")
        if not twitter_data.get("followers_count") and prev_twitter.get("followers_count"):
            twitter_data["followers_count"] = prev_twitter.get("followers_count", 0)

    data["twitter"] = twitter_data

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        log.info(f"data.json updated – {len(twitter_data['recent_posts'])} posts.")
    except Exception as e:
        log.error(f"Write failed: {e}")

    # Sync to public/data.json for Vite dev server
    public_data = _BACKEND_DIR.parent / "public" / "data.json"
    try:
        public_data.parent.mkdir(parents=True, exist_ok=True)
        with open(public_data, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass

    log.info("=== Twitter Cycle Complete ===")


# ──────────────────────────────────────────────────────────
#  STANDALONE
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Standalone – fetching once then every 15 minutes.")
    while True:
        run_twitter_cycle()
        log.info("Sleeping 15 minutes ...")
        time.sleep(15 * 60)

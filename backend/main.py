import os
import sys
import shutil
import threading
from pathlib import Path

# Catalyst assigns the port via this env var
PORT = int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT", os.environ.get("PORT", 8080)))
print(f"[main] PORT={PORT} | sys.path={sys.path[:3]}", flush=True)

# In Docker, Playwright is pre-installed at /app/pw-browsers (set in Dockerfile ENV).
# setdefault keeps the Dockerfile ENV value if already set.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/tmp/pw-browsers")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("HOME", "/tmp")

_backend_dir = Path(__file__).resolve().parent

def _seed_tmp_data():
    """Ensure data.json and x_session.json are in /tmp for Catalyst/Linux."""
    if os.name == 'nt':
        return # Skip on local Windows
        
    try:
        # Seed data.json
        src_data = _backend_dir / "data.json"
        dest_data = Path("/tmp/data.json")
        if src_data.exists() and not dest_data.exists():
            shutil.copy2(str(src_data), "/tmp/data.json")
            print("[setup] ✓ Seeded /tmp/data.json from repo content.", flush=True)
            
        # Seed x_session.json
        src_session = _backend_dir / "x_session.json"
        dest_session = Path("/tmp/x_session.json")
        if src_session.exists() and not dest_session.exists():
            shutil.copy2(str(src_session), "/tmp/x_session.json")
            print("[setup] ✓ Seeded /tmp/x_session.json.", flush=True)
    except Exception as e:
        print(f"[setup] Seeding failed (non-fatal): {e}", flush=True)

def _background_setup():
    """Runs after Flask is listening — waits for Playwright, copies session, starts schedulers."""
    import time
    import glob
    # Give the server 30s to pass healthchecks before starting heavy browser tasks
    time.sleep(30)

    # Wait for the actual Chromium binary to exist (max 8 minutes)
    print("[setup] Waiting for Playwright Chromium binary...", flush=True)
    chromium_found = False
    for i in range(96):  # 96 x 5s = 8 minutes max
        pw_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/tmp/pw-browsers")
        matches = glob.glob(f"{pw_path}/**/chrome-headless-shell", recursive=True) + \
                  glob.glob(f"{pw_path}/**/chromium", recursive=True) + \
                  glob.glob(f"{pw_path}/**/chrome", recursive=True)
        if matches:
            print(f"[setup] ✓ Chromium binary found after {i*5}s: {matches[0]}", flush=True)
            chromium_found = True
            break
        if i % 6 == 0:
            print(f"[setup] Still waiting for Chromium... ({i*5}s elapsed)", flush=True)
        time.sleep(5)

    if not chromium_found:
        print("[setup] WARNING: Chromium not found after 8 min. Twitter fetch will be skipped.", flush=True)

    # Copy x_session.json from deploy dir to /tmp
    _src = _backend_dir / "x_session.json"
    if _src.exists():
        try:
            shutil.copy2(str(_src), "/tmp/x_session.json")
            print("[setup] ✓ x_session copied.", flush=True)
        except Exception as e:
            print(f"[setup] session copy failed: {e}", flush=True)

    try:
        from server import start_background_scheduler
        start_background_scheduler()
        print("[setup] ✓ Schedulers started.", flush=True)
    except Exception as e:
        print(f"[setup] Schedulers failed: {e}", flush=True)


from server import app

if __name__ == "__main__":
    print(f"[main] Starting Flask on {PORT}", flush=True)
    _seed_tmp_data()
    threading.Thread(target=_background_setup, daemon=True, name="bg-setup").start()
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

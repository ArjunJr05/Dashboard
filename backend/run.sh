#!/bin/sh

export PORT=${X_ZOHO_CATALYST_LISTEN_PORT:-${PORT:-8080}}
export PLAYWRIGHT_BROWSERS_PATH="/tmp/pw-browsers"
export XDG_CACHE_HOME="/tmp/.cache"
export HOME="/tmp"

echo "[run.sh] Python: $(python3 --version 2>&1)"
echo "[run.sh] Port: $PORT"

# 1. Fix PATH to include the local bin where gunicorn/flask are installed
export PATH="/tmp/.local/bin:$PATH"

# 2. Install ESSENTIAL dependencies (no-cache to save space)
echo "[run.sh] Installing core dependencies (space-saving mode)..."
python3 -m pip install flask flask-cors beautifulsoup4 requests gunicorn --user --quiet --no-cache-dir

# 3. Start the server IMMEDIATELY (using full path to gunicorn just in case)
echo "[run.sh] Starting server with Gunicorn on port $PORT..."
(
  # 4. Background tasks: Install rest + Playwright
  echo "[run.sh] Background tasks starting..." >> /tmp/run.log
  python3 -m pip install -r requirements.txt --user --quiet --no-cache-dir
  python3 -m pip install app-store-scraper --no-deps --user --quiet --no-cache-dir
  
  # Clear pip cache immediately to free up space for Playwright
  python3 -m pip cache purge > /dev/null 2>&1
  rm -rf /tmp/.cache/pip
  
  # Install ONLY Chromium (saves ~400MB vs full install)
  python3 -m playwright install chromium
  
  echo "[run.sh] Background tasks complete." >> /tmp/run.log
  touch /tmp/pw-ready
) &

# Use the full path to gunicorn to be 100% sure
exec /tmp/.local/bin/gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 server:app


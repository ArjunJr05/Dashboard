#!/bin/sh

export PORT=${X_ZOHO_CATALYST_LISTEN_PORT:-${PORT:-8080}}
export PLAYWRIGHT_BROWSERS_PATH="/tmp/pw-browsers"
export XDG_CACHE_HOME="/tmp/.cache"
export HOME="/tmp"

echo "[run.sh] Python: $(python3 --version 2>&1)"
echo "[run.sh] Port: $PORT"

# Install ESSENTIAL dependencies only (fast)
echo "[run.sh] Installing core dependencies..."
python3 -m pip install flask flask-cors beautifulsoup4 requests --user --quiet

# Start the server IMMEDIATELY in the foreground
# The Twitter and News schedulers already have built-in delays (30s)
# to wait for background tasks like playwright and remaining pip installs.
echo "[run.sh] Starting server to bind port..."
(
  # Install the rest in the background
  python3 -m pip install -r requirements.txt --user --quiet
  python3 -m pip install app-store-scraper --no-deps --user --quiet
  
  # Install Playwright
  python3 -m playwright install chromium
  python3 -m playwright install-deps chromium || true
  
  echo "[run.sh] Background deps and Playwright complete."
  touch /tmp/pw-ready
) &

# Start the server IMMEDIATELY using Gunicorn (production grade)
echo "[run.sh] Starting server with Gunicorn on port $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 server:app


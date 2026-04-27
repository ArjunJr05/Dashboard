#!/bin/sh

export PORT=${X_ZOHO_CATALYST_LISTEN_PORT:-${PORT:-8080}}
export PLAYWRIGHT_BROWSERS_PATH="/tmp/pw-browsers"
export XDG_CACHE_HOME="/tmp/.cache"
export HOME="/tmp"

echo "[run.sh] Python: $(python3 --version 2>&1)"
echo "[run.sh] Port: $PORT"

# Install Python dependencies (fast, must finish before server starts)
echo "[run.sh] Installing Python dependencies..."
python3 -m pip install -r requirements.txt --user --quiet 2>&1 | tail -5
python3 -m pip install app-store-scraper --no-deps --user --quiet
echo "[run.sh] Python deps done."

# Install Playwright Chromium IN THE BACKGROUND so server can start immediately.
# Catalyst kills the process if it doesn't bind to the port within ~30 seconds.
# The Twitter scheduler will wait until Chromium is ready before running.
if [ ! -d "/tmp/pw-browsers" ]; then
  echo "[run.sh] Playwright not found — installing in background..."
  (
    python3 -m playwright install chromium >> /tmp/pw-install.log 2>&1
    python3 -m playwright install-deps chromium >> /tmp/pw-install.log 2>&1 || true
    echo "[run.sh] Playwright background install complete." >> /tmp/pw-install.log
    touch /tmp/pw-ready
  ) &
else
  echo "[run.sh] Playwright already installed."
  touch /tmp/pw-ready
fi

echo "[run.sh] Starting server..."
exec python3 main.py


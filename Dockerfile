# ═══════════════════════════════════════════════════════════════
# Python backend + Playwright Chromium
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim

# ── System libs required by Playwright / Chromium + Build tools for pip ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg \
    build-essential gcc python3-dev libffi-dev libssl-dev \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 \
    libx11-6 libx11-xcb1 libxcb1 libxext6 libxss1 \
    fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ───────────────────────────────────────────
WORKDIR /app/backend

# ── Python dependencies (Split to identify failures) ──────────
COPY backend/requirements.txt ./
RUN pip install --upgrade pip
RUN pip install flask flask-cors requests beautifulsoup4 schedule gunicorn Pillow
RUN pip install google-play-scraper app_store_scraper
RUN pip install playwright
RUN pip install zcatalyst-sdk
RUN pip install greenlet pyee

# ── Install Playwright Chromium at BUILD time ───────────────────
# Baked into the image so no download needed on every container start
ENV PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers
RUN playwright install chromium && \
    playwright install-deps chromium || true

# ── Copy backend source ─────────────────────────────────────────
COPY backend/ ./

# ── Environment variables ───────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers \
    HOME=/root \
    ENABLE_CATALYST_UPLOAD=1

# ── Port ────────────────────────────────────────────────────────
EXPOSE 8080

# ── Start ───────────────────────────────────────────────────────
# X_ZOHO_CATALYST_LISTEN_PORT is injected by Zoho Catalyst at runtime.
# Falls back to PORT, then 8080 for local testing.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${X_ZOHO_CATALYST_LISTEN_PORT:-${PORT:-8080}} --workers 1 --threads 4 --timeout 0 server:app"]

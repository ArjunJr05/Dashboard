# 📰 Arattai News Dashboard

A high-performance, visually stunning review and news dashboard designed for the **Arattai** ecosystem. This project integrates real-time sentiment analysis from the App Store and Google Play Store, along with an automated **X (Twitter) Feed** scraper using Playwright.

---

## 🚀 Key Features

*   **Dynamic Slide Show**: Automated rotation between App Store reviews, Play Store reviews, Latest News, and X Feed.
*   **X (Twitter) Integration**: Captures full-context screenshots of X posts and comments.
*   **Sentiment Tracking**: Real-time visualization of user feedback (Neutral, Happy, Ecstatic, Frustrated, Angry).
*   **Session Management**: Built-in UI to manage X login sessions manually to bypass bot detection.
*   **Multi-Platform Hosting**: Ready for **Zoho Catalyst (AppSail)** or **Docker** containers.

---

## 🛠️ Tech Stack

### Frontend
*   **Vue 3 (Composition API)**: Core application logic.
*   **Vite**: Ultra-fast build tool.
*   **Vanilla CSS**: High-end custom aesthetics with glassmorphism and micro-animations.

### Backend
*   **Python (Flask)**: Lightweight API serving data and screenshots.
*   **Playwright**: Headless browser automation for reliable X scraping.
*   **Zoho Catalyst SDK**: For cloud-native deployment and file management.

---

## 📦 Local Setup

### 1. Prerequisites
*   Node.js 20+
*   Python 3.9+
*   Playwright Browsers

### 2. Frontend Setup
```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

### 3. Backend Setup
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python main.py
```

---

## 🐳 Docker Deployment

The project includes a multi-stage `Dockerfile` that builds the frontend and bundles it into the Python backend for a single-container deployment.

### Build and Run
```bash
# Build the image
docker build -t arattai-dashboard .

# Run the container
docker run -p 8080:8080 arattai-dashboard
```

---

## ☁️ Zoho Catalyst Deployment

### 1. Build Frontend
```bash
npm run build
cp client/client-package.json dist/
```

### 2. Deploy
```bash
# For Development
catalyst deploy

# For Production (Paid Version)
catalyst deploy --env production
```

---

## 🐦 Twitter Session Management

To ensure X screenshots work without being blocked:
1.  Open the dashboard.
2.  Click the **Settings (⚙)** icon in the bottom-right.
3.  Click **"Login to X"**.
4.  A manual login window will open. Complete the login on your server/machine.
5.  The dashboard will save the `x_session.json` and use it for all future background scrapes.

---

## 📂 Project Structure

```text
├── backend/
│   ├── main.py            # Entry point for AppSail
│   ├── server.py          # Flask routes and Scheduler
│   ├── twitter_fetcher.py # Playwright scraping logic
│   ├── data.json          # Live dashboard data
│   └── public/            # Static files for AppSail
├── src/
│   ├── App.vue            # Main Frontend Component
│   └── main.js            # Vue entry point
├── catalyst.json          # Zoho Catalyst config
└── Dockerfile             # Multi-stage Docker config
```

---

## 📝 License
Proprietary for Arattai News Dashboard.

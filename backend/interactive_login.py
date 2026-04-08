"""
Interactive X login helper
Run this once to save your authenticated session for reuse by twitter_fetcher.py

Usage: python interactive_login.py
Then manually log into X in the browser window that opens
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

_BACKEND_DIR = Path(__file__).resolve().parent
SESSION_FILE = str(_BACKEND_DIR / "x_session.json")

def interactive_login():
    """Open browser in headful mode for manual login, save session"""
    
    print("\n" + "="*60)
    print("X (Twitter) Interactive Login Helper")
    print("="*60)
    print("\nA browser window will open shortly.")
    print("Please log into your X account manually.")
    print("Once logged in, the browser will STAY OPEN for 120 seconds.")
    print("Then it will automatically close and save your session.")
    print("\n" + "="*60 + "\n")
    
    with sync_playwright() as pw:
        # Launch in HEADFUL mode (not headless) so user can interact
        browser = pw.chromium.launch(
            headless=False,  # Show browser window
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
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
        
        # Navigate to X
        print("[*] Opening X login page...")
        page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)
        
        print("\n✓ Browser opened. Please log in manually now.")
        print("  You have 120 seconds after logging in.")
        print("  The browser will auto-close and save your session.\n")
        
        # Wait for user to complete login
        import time
        time.sleep(120)
        
        # Save the session
        print("\n[*] Saving authenticated session...")
        storage = context.storage_state()
        
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(storage, f, indent=2)
            print(f"✓ Session saved to: {SESSION_FILE}")
            print("\nYou can now close this window.")
            print("Future twitter_fetcher.py runs will use this session!")
        except Exception as e:
            print(f"✗ Failed to save session: {e}")
        
        browser.close()

if __name__ == "__main__":
    interactive_login()

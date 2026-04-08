# twitter_screenshotter.py
# ─────────────────────────────────────────────────────────────
# DEPRECATED: This file has been superseded by twitter_fetcher.py
# which handles login, screenshots, comments, AND Catalyst upload
# in one clean module called automatically every 15 minutes.
#
# Run the new fetcher instead:
#   python twitter_fetcher.py
# ─────────────────────────────────────────────────────────────
from twitter_fetcher import run_twitter_cycle

if __name__ == "__main__":
    import time
    while True:
        run_twitter_cycle()
        print("Sleeping 15 minutes …")
        time.sleep(15 * 60)

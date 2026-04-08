"""
enrich_reviews.py
─────────────────
Uses Catalyst Qwen 3-30B A3B to classify reviews with:
  - sentiment: Neutral | Happy | Ecstatic | Frustrated | Angry
  - timing: integer seconds a human would take to read the review

Sends BOTH appstore (max 10) and playstore (max 10) in ONE single prompt
to avoid rate limits. Output is merged back into data.json.

Also enriches X/Twitter comments with sentiment + timing.

Run this after fetching reviews (called by z1.py run_fetch_cycle).
Also callable standalone: python enrich_reviews.py
"""

import os, json, time, requests
from datetime import datetime

# ── Catalyst Qwen Config ──────────────────────────────────────────────────────
CATALYST_ORG = "60064252849"
CATALYST_URL = (
    "https://api.catalyst.zoho.in/quickml/v2"
    "/project/28618000000061001/llm/chat"
)
CATALYST_TOKEN = os.environ.get("CATALYST_TOKEN", "")

MAX_REVIEWS_PER_PLATFORM = 10

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
if os.name != "nt":
    DATA_FILE = "/tmp/data.json"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fallback_sentiment(rating: int, body: str = "") -> str:
    # ── Keywords help when the rating is misleading ──
    b = (body or "").lower()
    neg_keys = ["disappointed", "failed", "slow", "wait", "stutter", "muffled", "unable", "worst", "unusable", "not working"]
    if any(k in b for k in neg_keys):
        return "frustrated" if rating >= 3 else "angry"
    
    if rating >= 5: return "ecstatic"
    if rating >= 4: return "happy"
    if rating == 3: return "neutral"
    if rating == 2: return "frustrated"
    return "angry"

def fallback_timing(body: str) -> int:
    """Average adult reads ~200 words/min → ~3 words/sec. Min 2 seconds."""
    words = len((body or "").split())
    return max(2, round(words / 3))

# ── Single combined LLM call ───────────────────────────────────────────────────
def enrich_all_reviews(appstore_reviews: list, playstore_reviews: list) -> tuple[list, list]:
    """
    Sends up to 10 appstore + 10 playstore reviews in ONE prompt.
    Returns (enriched_appstore, enriched_playstore) with 'sentiment' and 'timing' added.
    """
    ios_slice = appstore_reviews[:MAX_REVIEWS_PER_PLATFORM]
    and_slice = playstore_reviews[:MAX_REVIEWS_PER_PLATFORM]

    total = len(ios_slice) + len(and_slice)
    print(f"[{now()}] [enrich] Preparing LLM prompt: {len(ios_slice)} App Store + {len(and_slice)} Play Store = {total} reviews")

    # Build numbered review list  (ios: I1..I10, android: A1..A10)
    lines = []
    for i, r in enumerate(ios_slice):
        lines.append(f"I{i+1}. [{r.get('rating','?')}★] {(r.get('body') or '')[:400]}")
    for i, r in enumerate(and_slice):
        lines.append(f"A{i+1}. [{r.get('rating','?')}★] {(r.get('body') or '')[:400]}")

    reviews_block = "\n".join(lines)

    system_prompt = (
        "You are a review analysis engine. "
        "For each review, you will classify TWO things:\n\n"
        "1. sentiment — pick EXACTLY ONE from: Neutral, Happy, Ecstatic, Frustrated, Angry\n"
        "   Rules (PRIORITIZE TEXT CONTENT OVER STAR RATING):\n"
        "   - Very ecstatic/amazing text → Ecstatic (ignore rating if text is overwhelmingly positive)\n"
        "   - Positive/satisfied text → Happy\n"
        "   - Mixed, neutral, or very short generic text → Neutral\n"
        "   - Complaints, technical issues, or 'disappointed' text → Frustrated (even if rating is 4-5★)\n"
        "   - Angry, hateful, or extremely negative text → Angry (even if rating is high by mistake)\n"
        "   Note: A user might give 4 stars but say 'very disappointed'. You MUST classify this based on the text (Frustrated), not the stars.\n\n"
        "2. timing — integer seconds an average adult human would need to READ the review body.\n"
        "   Average reading speed: 200 words/min (~3 words/sec).\n"
        "   Minimum: 2 seconds. Round to nearest whole number.\n"
        "   Examples: 'good' → 2, 'nice app' → 2, a 30-word review → 10, a 100-word review → 20.\n\n"
        "Output ONLY a valid JSON array — no markdown, no explanation, no extra text.\n"
        "Each element: {\"id\": \"<original id like I1 or A3>\", \"sentiment\": \"<value>\", \"timing\": <number>}\n"
        "Output ALL reviews in the SAME array. Do not split into groups."
    )

    user_prompt = (
        f"Classify ALL {total} reviews below.\n\n"
        + reviews_block
        + "\n\nRespond ONLY with a JSON array."
    )

    print(f"[{now()}] [enrich] Calling Qwen 3-30B A3B via Catalyst...")
    raw = _call_qwen(system_prompt, user_prompt)
    print(f"[{now()}] [enrich] LLM response received ({len(raw)} chars)")

    # Parse response
    result_map: dict[str, dict] = {}
    try:
        clean = raw.strip()
        # Strip markdown fences if present
        if clean.startswith("```"):
            clean = clean.split("```", 2)[-1] if clean.count("```") >= 2 else clean
            clean = clean.lstrip("json").strip().rstrip("```").strip()
        parsed = json.loads(clean)
        for item in parsed:
            rid = item.get("id", "")
            result_map[rid] = {
                "sentiment": str(item.get("sentiment", "Neutral")).strip(),
                "timing": int(item.get("timing", 2)),
            }
        print(f"[{now()}] [enrich] Parsed {len(result_map)} classifications from LLM")
    except Exception as e:
        print(f"[{now()}] [enrich] WARNING: Failed to parse LLM JSON: {e}")
        print(f"[{now()}] [enrich] Raw output (first 500 chars): {raw[:500]}")
        print(f"[{now()}] [enrich] Falling back to heuristics for all reviews")

    # Validate sentiment values
    valid_sentiments = {"Neutral", "Happy", "Ecstatic", "Frustrated", "Angry"}

    def safe_sentiment(val: str, r: dict) -> str:
        if val in valid_sentiments:
            return val
        # Case-insensitive fix
        for vs in valid_sentiments:
            if val.lower() == vs.lower():
                return vs
        print(f"[{now()}] [enrich] Unknown sentiment '{val}', using fallback")
        return fallback_sentiment(r.get("rating", 3), r.get("body", "")).capitalize()

    def safe_timing(val, body: str) -> int:
        try:
            t = int(val)
            return max(2, t)
        except Exception:
            return fallback_timing(body)

    # Enrich ios reviews
    enriched_ios = []
    for i, r in enumerate(ios_slice):
        rid = f"I{i+1}"
        classification = result_map.get(rid, {})
        raw_sent = classification.get("sentiment", fallback_sentiment(r.get("rating", 3), r.get("body", "")).capitalize())
        raw_timing = classification.get("timing", fallback_timing(r.get("body", "")))
        enriched = dict(r)
        enriched["sentiment"] = safe_sentiment(raw_sent, r)
        enriched["timing"] = safe_timing(raw_timing, r.get("body", ""))
        enriched_ios.append(enriched)
        print(f"[{now()}] [enrich]   iOS   {rid}: author={r.get('author','?')[:20]!r:22} → sentiment={enriched['sentiment']:12} timing={enriched['timing']}s")

    # Enrich android reviews
    enriched_and = []
    for i, r in enumerate(and_slice):
        rid = f"A{i+1}"
        classification = result_map.get(rid, {})
        raw_sent = classification.get("sentiment", fallback_sentiment(r.get("rating", 3), r.get("body", "")).capitalize())
        raw_timing = classification.get("timing", fallback_timing(r.get("body", "")))
        enriched = dict(r)
        enriched["sentiment"] = safe_sentiment(raw_sent, r)
        enriched["timing"] = safe_timing(raw_timing, r.get("body", ""))
        enriched_and.append(enriched)
        print(f"[{now()}] [enrich]   Android {rid}: author={r.get('author','?')[:20]!r:22} → sentiment={enriched['sentiment']:12} timing={enriched['timing']}s")

    # Any remaining reviews beyond limit: fallback only (no LLM, no extra cost)
    for r in appstore_reviews[MAX_REVIEWS_PER_PLATFORM:]:
        enriched = dict(r)
        if "sentiment" not in enriched:
            enriched["sentiment"] = fallback_sentiment(r.get("rating", 3), r.get("body", "")).capitalize()
        if "timing" not in enriched:
            enriched["timing"] = fallback_timing(r.get("body", ""))
        enriched_ios.append(enriched)

    for r in playstore_reviews[MAX_REVIEWS_PER_PLATFORM:]:
        enriched = dict(r)
        if "sentiment" not in enriched:
            enriched["sentiment"] = fallback_sentiment(r.get("rating", 3), r.get("body", "")).capitalize()
        if "timing" not in enriched:
            enriched["timing"] = fallback_timing(r.get("body", ""))
        enriched_and.append(enriched)

    return enriched_ios, enriched_and


# ── X/Twitter comment sentiment + timing enrichment ─────────────────────────
def enrich_twitter_comments(recent_posts: list) -> list:
    """
    For each post in recent_posts, enrich every comment with:
      - 'sentiment': one of Neutral | Happy | Ecstatic | Frustrated | Angry
      - 'timing': integer seconds to read the comment
    Uses the same 5-sentiment system as playstore/appstore reviews.
    Returns the updated recent_posts list.
    """
    # Collect all comments that need enrichment
    pending = []  # list of (post_idx, comment_idx, body)
    for pi, post in enumerate(recent_posts):
        for ci, comment in enumerate(post.get("comments", [])):
            needs_sentiment = "sentiment" not in comment or not comment["sentiment"]
            needs_timing    = "timing" not in comment or comment["timing"] is None
            if needs_sentiment or needs_timing:
                body = (comment.get("body") or "").strip()
                pending.append((pi, ci, body))

    if not pending:
        print(f"[{now()}] [enrich-x] All X comments already have sentiment+timing — skipping LLM call.")
        return recent_posts

    total = len(pending)
    print(f"[{now()}] [enrich-x] Enriching {total} X comment(s) with sentiment+timing via Qwen...")

    # Build prompt lines: X1, X2, ...
    lines = []
    for idx, (pi, ci, body) in enumerate(pending):
        lines.append(f"X{idx+1}. {body[:400]}")

    comments_block = "\n".join(lines)

    system_prompt = (
        "You are a social media comment analysis engine. "
        "For each X (Twitter) comment, classify TWO things:\n\n"
        "1. sentiment — pick EXACTLY ONE from: Neutral, Happy, Ecstatic, Frustrated, Angry\n"
        "   Rules (judge based on the comment text):\n"
        "   - Very positive/enthusiastic/loving text → Ecstatic\n"
        "   - Positive/satisfied/supportive text → Happy\n"
        "   - Mixed, neutral, short generic, or informational text → Neutral\n"
        "   - Complaints, negative feedback, or disappointed text → Frustrated\n"
        "   - Angry, hateful, or extremely negative text → Angry\n\n"
        "2. timing — integer seconds an average adult needs to READ that comment.\n"
        "   Reading speed: 200 words/min (~3 words/sec). Minimum 2 seconds.\n"
        "   Examples: 'good' → 2, 'nice app' → 2, 30-word text → 10, 100-word text → 20.\n\n"
        "Output ONLY a valid JSON array — no markdown, no explanation, no extra text.\n"
        "Each element: {\"id\": \"<id like X1>\", \"sentiment\": \"<value>\", \"timing\": <integer>}"
    )

    user_prompt = (
        f"Classify ALL {total} X comments below.\n\n"
        + comments_block
        + "\n\nRespond ONLY with a JSON array."
    )

    print(f"[{now()}] [enrich-x] Calling Qwen for X comment sentiment+timing...")
    raw = _call_qwen(system_prompt, user_prompt)
    print(f"[{now()}] [enrich-x] LLM response received ({len(raw)} chars)")

    # Parse result
    result_map: dict[str, dict] = {}
    valid_sentiments = {"Neutral", "Happy", "Ecstatic", "Frustrated", "Angry"}
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 2)[-1] if clean.count("```") >= 2 else clean
            clean = clean.lstrip("json").strip().rstrip("```").strip()
        parsed = json.loads(clean)
        for item in parsed:
            rid = item.get("id", "")
            sent = str(item.get("sentiment", "Neutral")).strip()
            # case-insensitive match
            matched = next((v for v in valid_sentiments if v.lower() == sent.lower()), "Neutral")
            try:
                timing = max(2, int(item.get("timing", 2)))
            except Exception:
                timing = 2
            result_map[rid] = {"sentiment": matched, "timing": timing}
        print(f"[{now()}] [enrich-x] Parsed {len(result_map)} sentiment+timing values from LLM")
    except Exception as e:
        print(f"[{now()}] [enrich-x] WARNING: Failed to parse LLM JSON: {e}")
        print(f"[{now()}] [enrich-x] Raw (first 500): {raw[:500]}")
        print(f"[{now()}] [enrich-x] Falling back to heuristics for all X comments")

    # Apply sentiment + timing back
    for idx, (pi, ci, body) in enumerate(pending):
        rid = f"X{idx+1}"
        classification = result_map.get(rid, {})
        sentiment = classification.get("sentiment") or fallback_sentiment(3, body).capitalize()
        timing    = classification.get("timing")    or fallback_timing(body)
        recent_posts[pi]["comments"][ci]["sentiment"] = sentiment
        recent_posts[pi]["comments"][ci]["timing"]    = timing
        author = recent_posts[pi]["comments"][ci].get("author", "?")[:20]
        print(f"[{now()}] [enrich-x]   {rid}: author={author!r:22} → sentiment={sentiment:12} timing={timing}s")

    return recent_posts


def _call_qwen(system_prompt: str, user_prompt: str) -> str:
    """Make a single call to the Catalyst Qwen 3-30B A3B endpoint."""
    if not CATALYST_TOKEN:
        print(f"[{now()}] [enrich] WARNING: CATALYST_TOKEN not set — skipping LLM, using fallback")
        return "[]"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Zoho-oauthtoken {CATALYST_TOKEN}",
        "CATALYST-ORG": CATALYST_ORG,
    }
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,  # enough for 20 reviews
    }
    try:
        print(f"[{now()}] [enrich] POST {CATALYST_URL}")
        start = time.time()
        r = requests.post(CATALYST_URL, headers=headers, json=payload, timeout=90)
        elapsed = round(time.time() - start, 2)
        print(f"[{now()}] [enrich] Response HTTP {r.status_code} in {elapsed}s")

        if r.ok:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return content
        else:
            print(f"[{now()}] [enrich] ERROR: HTTP {r.status_code}: {r.text[:300]}")
            return "[]"
    except Exception as e:
        print(f"[{now()}] [enrich] EXCEPTION calling Qwen: {e}")
        return "[]"


def run_enrichment(data_file: str = DATA_FILE) -> bool:
    """
    Load data.json, enrich reviews with sentiment+timing, save back.
    Returns True on success, False on failure.
    """
    print(f"\n[{now()}] ══════════════════════════════════")
    print(f"[{now()}] STARTING REVIEW ENRICHMENT (LLM)")
    print(f"[{now()}] Data file: {data_file}")
    print(f"[{now()}] ══════════════════════════════════")

    # Load data.json
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[{now()}] [enrich] Loaded data.json successfully")
    except FileNotFoundError:
        print(f"[{now()}] [enrich] ERROR: {data_file} not found. Run z1.py first to fetch reviews.")
        return False
    except json.JSONDecodeError as e:
        print(f"[{now()}] [enrich] ERROR: data.json is invalid JSON: {e}")
        return False

    appstore_reviews  = data.get("appstore",  {}).get("reviews", [])
    playstore_reviews = data.get("playstore", {}).get("reviews", [])

    print(f"[{now()}] [enrich] Found {len(appstore_reviews)} App Store reviews, {len(playstore_reviews)} Play Store reviews")

    if not appstore_reviews and not playstore_reviews:
        print(f"[{now()}] [enrich] WARNING: No reviews found in data.json — nothing to enrich")
        return False

    # Run enrichment
    enriched_ios, enriched_and = enrich_all_reviews(appstore_reviews, playstore_reviews)

    # Write back
    data["appstore"]["reviews"]  = enriched_ios
    data["playstore"]["reviews"] = enriched_and
    data["last_enriched"] = now()

    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{now()}] [enrich] ✓ data.json saved with sentiment + timing for all reviews")
    except Exception as e:
        print(f"[{now()}] [enrich] ERROR: Failed to write data.json: {e}")
        return False

    # Also sync to public/data.json
    public_data_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "public", "data.json"
    )
    try:
        with open(public_data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{now()}] [enrich] ✓ public/data.json synced")
    except Exception as e:
        print(f"[{now()}] [enrich] INFO: Could not sync public/data.json: {e} (non-fatal)")

    print(f"[{now()}] ENRICHMENT COMPLETE")
    print(f"[{now()}] ══════════════════════════════════\n")
    return True


def run_twitter_enrichment(data_file: str = DATA_FILE) -> bool:
    """
    Load data.json, enrich X/Twitter comment timing via LLM, save back.
    Only processes comments that are missing the 'timing' field.
    Returns True on success, False on failure.
    """
    print(f"\n[{now()}] ══════════════════════════════════")
    print(f"[{now()}] STARTING X COMMENT TIMING ENRICHMENT")
    print(f"[{now()}] Data file: {data_file}")
    print(f"[{now()}] ══════════════════════════════════")

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[{now()}] [enrich-x] ERROR: {data_file} not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"[{now()}] [enrich-x] ERROR: data.json is invalid JSON: {e}")
        return False

    recent_posts = data.get("twitter", {}).get("recent_posts", [])
    if not recent_posts:
        print(f"[{now()}] [enrich-x] No X posts found in data.json — skipping.")
        return False

    total_comments = sum(len(p.get("comments", [])) for p in recent_posts)
    print(f"[{now()}] [enrich-x] Found {len(recent_posts)} posts with {total_comments} total comments")

    enriched_posts = enrich_twitter_comments(recent_posts)
    data["twitter"]["recent_posts"] = enriched_posts
    data["last_twitter_enriched"] = now()

    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{now()}] [enrich-x] ✓ data.json saved with sentiment+timing for all X comments")
    except Exception as e:
        print(f"[{now()}] [enrich-x] ERROR: Failed to write data.json: {e}")
        return False

    # Sync to public/data.json
    public_data_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "public", "data.json"
    )
    try:
        with open(public_data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{now()}] [enrich-x] ✓ public/data.json synced")
    except Exception as e:
        print(f"[{now()}] [enrich-x] INFO: Could not sync public/data.json: {e} (non-fatal)")

    print(f"[{now()}] X COMMENT SENTIMENT+TIMING ENRICHMENT COMPLETE")
    print(f"[{now()}] ══════════════════════════════════\n")
    return True


# ── Standalone entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    # Step 1: Enrich App Store + Play Store reviews (sentiment + timing)
    success = run_enrichment()
    if not success:
        print(f"[{now()}] Review enrichment failed — check logs above")
        exit(1)

    # Step 2: Enrich X/Twitter comments (sentiment + timing)
    # This is the most commonly missed step — run it every time standalone
    x_success = run_twitter_enrichment()
    if not x_success:
        print(f"[{now()}] X comment enrichment failed — check logs above")
        # Non-fatal: reviews are already saved, don't exit

    print(f"[{now()}] All enrichment complete.")

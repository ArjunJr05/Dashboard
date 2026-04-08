"""
ai_review_analysis.py
─────────────────────
Uses the Zoho Catalyst Qwen 3-30B A3B model to:
  1. Classify each Android review into one of 5 tiers:
       Unsatisfactory | Satisfactory | Good | Excellent | Outstanding
  2. Classify each iOS review into positive | neutral | negative
  3. Return structured bubble/badge data for the frontend

Endpoint: GET /ai-review-analysis
"""

import os, json, time, requests
from flask import Blueprint, jsonify, request as flask_request

# ── Catalyst Qwen Config ──────────────────────────────────────────────────────
CATALYST_ORG   = "60064252849"
CATALYST_URL   = (
    "https://api.catalyst.zoho.in/quickml/v2"
    f"/project/28618000000061001/llm/chat"
)

# Token is injected via env-var in production (Catalyst App Secret / OAuth token).
# For local dev, set CATALYST_TOKEN in your shell.
CATALYST_TOKEN = os.environ.get("CATALYST_TOKEN", "")

# ── 5-tier mapping ────────────────────────────────────────────────────────────
ANDROID_TIERS = {
    "Unsatisfactory": {"emoji": "😤", "color": "#ff4757", "rank": 1},
    "Satisfactory":   {"emoji": "😐", "color": "#ffa502", "rank": 2},
    "Good":           {"emoji": "🙂", "color": "#eccc68", "rank": 3},
    "Excellent":      {"emoji": "😄", "color": "#2ed573", "rank": 4},
    "Outstanding":    {"emoji": "🤩", "color": "#1e90ff", "rank": 5},
}

IOS_TIERS = {
    "negative": {"emoji": "👎", "color": "#ff4757", "label": "Negative"},
    "neutral":  {"emoji": "😶", "color": "#ffa502", "label": "Neutral"},
    "positive": {"emoji": "👍", "color": "#2ed573", "label": "Positive"},
}

# ── Blueprint ────────────────────────────────────────────────────────────────
analysis_bp = Blueprint("ai_analysis", __name__)


def qwen_classify_android(reviews: list[dict]) -> list[dict]:
    """
    Send a batch of Android reviews to Qwen and get 5-tier labels back.
    Returns the reviews list with an added 'tier' key.
    """
    if not reviews:
        return []

    # Build a compact numbered list for the prompt
    numbered = "\n".join(
        f"{i+1}. [{r.get('rating','?')}★] {r.get('body','')[:300]}"
        for i, r in enumerate(reviews)
    )

    system_prompt = (
        "You are a review classification engine. "
        "For each review given, output ONLY a JSON array (no markdown, no explanation) "
        "where each element is an object with keys 'index' (1-based) and 'tier'. "
        "Allowed tiers: Unsatisfactory, Satisfactory, Good, Excellent, Outstanding. "
        "Base your classification on the content AND the star rating:\n"
        "  1-star  → mostly Unsatisfactory\n"
        "  2-star  → mostly Satisfactory\n"
        "  3-star  → mostly Good\n"
        "  4-star  → mostly Excellent\n"
        "  5-star  → mostly Outstanding\n"
        "But use the text to upgrade/downgrade by one tier if warranted."
    )

    user_prompt = (
        f"Classify these {len(reviews)} Android Play Store reviews:\n\n"
        + numbered
        + "\n\nRespond with ONLY a JSON array like: "
        + '[{"index":1,"tier":"Outstanding"},{"index":2,"tier":"Good"},...]'
    )

    result = _call_qwen(system_prompt, user_prompt)

    # Merge tier back into reviews
    tier_map = {}
    try:
        clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        for item in parsed:
            tier_map[item["index"]] = item["tier"]
    except Exception as e:
        print(f"[ai_analysis] Failed to parse android tiers: {e}\nRaw: {result[:200]}")

    enriched = []
    for i, r in enumerate(reviews):
        tier = tier_map.get(i + 1, _fallback_tier(r.get("rating", 3)))
        if tier not in ANDROID_TIERS:
            tier = _fallback_tier(r.get("rating", 3))
        enriched.append({**r, "tier": tier, **ANDROID_TIERS[tier]})

    return enriched


def qwen_classify_ios(reviews: list[dict]) -> list[dict]:
    """
    Send a batch of iOS reviews to Qwen and get positive/neutral/negative labels.
    Returns the reviews list with added 'sentiment' key.
    """
    if not reviews:
        return []

    numbered = "\n".join(
        f"{i+1}. [{r.get('rating','?')}★] {r.get('body','')[:300]}"
        for i, r in enumerate(reviews)
    )

    system_prompt = (
        "You are a sentiment classification engine. "
        "For each review, output ONLY a JSON array (no markdown, no explanation) "
        "where each element is {'index': <1-based>, 'sentiment': <'positive'|'neutral'|'negative'>}. "
        "Use star rating as a strong signal: 4-5 → positive, 3 → neutral, 1-2 → negative. "
        "Override by one step if the text strongly contradicts the rating."
    )

    user_prompt = (
        f"Classify these {len(reviews)} iOS App Store reviews:\n\n"
        + numbered
        + "\n\nRespond ONLY with a JSON array."
    )

    result = _call_qwen(system_prompt, user_prompt)

    sent_map = {}
    try:
        clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        for item in parsed:
            sent_map[item["index"]] = item["sentiment"]
    except Exception as e:
        print(f"[ai_analysis] Failed to parse ios sentiment: {e}\nRaw: {result[:200]}")

    enriched = []
    for i, r in enumerate(reviews):
        rating = r.get("rating", 4)
        if rating >= 4:
            default_sent = "positive"
        elif rating == 3:
            default_sent = "neutral"
        else:
            default_sent = "negative"
        sentiment = sent_map.get(i + 1, default_sent)
        if sentiment not in IOS_TIERS:
            sentiment = default_sent
        tier_info = IOS_TIERS[sentiment]
        enriched.append({**r, "sentiment": sentiment, **tier_info})

    return enriched


def _call_qwen(system_prompt: str, user_prompt: str) -> str:
    """Make a single call to the Catalyst Qwen endpoint."""
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
        "max_tokens": 1024,
    }
    try:
        r = requests.post(CATALYST_URL, headers=headers, json=payload, timeout=30)
        if r.ok:
            data = r.json()
            # Standard OpenAI-compatible response from Catalyst
            return data["choices"][0]["message"]["content"]
        else:
            print(f"[ai_analysis] Qwen HTTP {r.status_code}: {r.text[:200]}")
            return "[]"
    except Exception as e:
        print(f"[ai_analysis] Qwen call failed: {e}")
        return "[]"


def _fallback_tier(rating) -> str:
    """Star-rating-only fallback when AI call fails."""
    try:
        r = int(rating)
    except Exception:
        r = 3
    mapping = {1: "Unsatisfactory", 2: "Satisfactory", 3: "Good", 4: "Excellent", 5: "Outstanding"}
    return mapping.get(r, "Good")


# ── Flask Route ───────────────────────────────────────────────────────────────
@analysis_bp.route("/ai-review-analysis")
def ai_review_analysis():
    """
    Returns AI-classified reviews split by platform.

    Query params:
      ?max=N   — max reviews per platform to classify (default 10, max 20)
    """
    # Load current data.json
    base_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    data_path = "/tmp/data.json" if os.name != "nt" else os.path.join(base_dir, "data.json")
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, "data.json")

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        return jsonify({"error": f"data.json not found: {e}"}), 500

    max_reviews = min(int(flask_request.args.get("max", 10)), 20)

    android_raw = (raw.get("playstore", {}).get("reviews") or [])[:max_reviews]
    ios_raw     = (raw.get("appstore",  {}).get("reviews") or [])[:max_reviews]

    # Classify — if token is missing, fall back to star-rating heuristic
    if CATALYST_TOKEN:
        android_classified = qwen_classify_android(android_raw)
        ios_classified     = qwen_classify_ios(ios_raw)
    else:
        # Graceful fallback: use star ratings only
        android_classified = [
            {**r, "tier": _fallback_tier(r.get("rating", 3)), **ANDROID_TIERS[_fallback_tier(r.get("rating", 3))]}
            for r in android_raw
        ]
        ios_classified = [
            {**r, "sentiment": "positive" if r.get("rating", 4) >= 4 else ("neutral" if r.get("rating") == 3 else "negative"),
             **IOS_TIERS["positive" if r.get("rating", 4) >= 4 else ("neutral" if r.get("rating") == 3 else "negative")]}
            for r in ios_raw
        ]

    # Build bubble summaries — count per tier
    android_bubble_counts = {tier: 0 for tier in ANDROID_TIERS}
    for r in android_classified:
        t = r.get("tier")
        if t in android_bubble_counts:
            android_bubble_counts[t] += 1

    ios_bubble_counts = {s: 0 for s in IOS_TIERS}
    for r in ios_classified:
        s = r.get("sentiment")
        if s in ios_bubble_counts:
            ios_bubble_counts[s] += 1

    android_bubbles = [
        {
            "tier":  tier,
            "emoji": ANDROID_TIERS[tier]["emoji"],
            "color": ANDROID_TIERS[tier]["color"],
            "rank":  ANDROID_TIERS[tier]["rank"],
            "count": android_bubble_counts[tier],
        }
        for tier in ANDROID_TIERS
    ]

    ios_bubbles = [
        {
            "sentiment": s,
            "label":     IOS_TIERS[s]["label"],
            "emoji":     IOS_TIERS[s]["emoji"],
            "color":     IOS_TIERS[s]["color"],
            "count":     ios_bubble_counts[s],
        }
        for s in IOS_TIERS
    ]

    return jsonify({
        "android": {
            "reviews": android_classified,
            "bubbles": android_bubbles,
            "meta": {
                "rating":       raw.get("playstore", {}).get("rating"),
                "rating_count": raw.get("playstore", {}).get("rating_count"),
            },
        },
        "ios": {
            "reviews": ios_classified,
            "bubbles": ios_bubbles,
            "meta": {
                "rating":       raw.get("appstore", {}).get("rating"),
                "rating_count": raw.get("appstore", {}).get("rating_count"),
            },
        },
        "ai_powered": bool(CATALYST_TOKEN),
    })

"""Linear agent orchestrator: gather data via Pandas tools → format via LLM (or deterministic fallback)."""
import re
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from tools import (
    get_alternatives,
    get_future_purchases,
    get_local_trends,
    get_peer_purchases,
    get_product_recommendations,
    get_upcoming_events,
    get_user_profile,
)
from config import MODEL_NAME

# ── Strict formatting prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a formatting assistant. Your job is to take the EXACT text provided by the tools and place it into the correct sections. Do not mix outputs. Do not write your own text.

RULES:
1. RecommendationTool output → "Recommended for You" ONLY.
2. FuturePurchaseTool output → "Next Likely Purchases" ONLY.
3. AlternativeFinderTool output → "Alternatives" ONLY.

OUTPUT TEMPLATE:
### Your Profile Summary
- [Age Group], interested in [Primary Interest], \\$[Budget] budget
- Prefers [Colors] and [Brand]
- Location: [Location]
- Upcoming Event: [Events]

### Local Trend & Peer Insight
- [Exact string from TrendTool]
- [Exact string from SocialTool]
- [Exact string from EventTool]

### Recommended for You
[Exact bullets from RecommendationTool]

### Next Likely Purchases
[Exact bullets from FuturePurchaseTool]

### Alternatives
[Exact bullets from AlternativeFinderTool]

*Disclaimer: Recommendations are based on synthetic demo data.*"""

# ── Formatting helpers ────────────────────────────────────────────────────────
def _bullets(text: str) -> list[str]:
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip().startswith("- ")]
    if lines:
        return lines
    nums = [f"- {m.strip()}" for m in re.findall(r"\d+\.\s(.*?)(?=\s\d+\.|$)", str(text))]
    return nums or [f"- {str(text).split(':', 1)[-1].strip()}"]

def _fallback(p: dict, t: str, s: str, ev: str, r: str, n: str, a: str) -> str:
    return "\n".join([
        "### Your Profile Summary",
        f"- {p.get('age_group', 'Adult')}, interested in {p.get('primary_interest', 'General')}, \\${p.get('budget', 'N/A')} budget",
        f"- Prefers {p.get('favorite_colors', 'N/A')} and {p.get('brand_affinity', 'N/A')}",
        f"- Location: {p.get('location', 'N/A')}",
        f"- Upcoming Event: {p.get('upcoming_events', 'None')}",
        "",
        "### Local Trend & Peer Insight",
        f"- {t}",
        f"- {s}",
        f"- {ev}",
        "",
        "### Recommended for You",
        *_bullets(r),
        "",
        "### Next Likely Purchases",
        *_bullets(n),
        "",
        "### Alternatives",
        *_bullets(a),
        "",
        "*Disclaimer: Recommendations are based on synthetic demo data.*",
    ])

# ── Main Orchestrator Function ────────────────────────────────────────────────
def run_agent(user_id: int = None, custom_profile: dict = None) -> str:
    """Executes the rule-based tools and formats the output via LLM."""
    
    # 1. Gather all context using Pandas tools
    p = get_user_profile.invoke({
        "user_id": user_id,
        "profile": custom_profile,
    })
    t = get_local_trends.invoke({"location": p.get("location", "")})
    s = (
        get_peer_purchases.invoke({"user_id": p.get("user_id", 0)})
        if p.get("user_id")
        else "Insight: Peer purchase signals are currently limited for new users."
    )
    ev = get_upcoming_events.invoke({"location": p.get("location", "")})
    r = get_product_recommendations.invoke({
        "budget": int(p.get("budget", 150)),
        "colors": p.get("favorite_colors", ""),
        "brand": p.get("brand_affinity", ""),
        "primary_interest": p.get("primary_interest", ""),
    })
    n = get_future_purchases.invoke({
        "budget": int(p.get("budget", 150)),
        "recommendations_data": r,
    })
    a = get_alternatives.invoke({
        "recommendations_data": r,
        "colors": p.get("favorite_colors", ""),
    })

    # 2. Build the fallback in case the LLM fails or goes rogue
    fb = _fallback(p, t, s, ev, r, n, a)

    # 3. Construct the LLM payload
    user_text = "\n".join([
        f"Age Group: {p.get('age_group', 'Adult')}",
        f"Primary Interest: {p.get('primary_interest', 'General')}",
        f"Budget: {p.get('budget', 'N/A')}",
        f"Location: {p.get('location', 'N/A')}",
        f"Brand: {p.get('brand_affinity', 'N/A')}",
        f"Colors: {p.get('favorite_colors', 'N/A')}",
        f"Past Purchases: {p.get('past_purchases', 'N/A')}",
        f"Upcoming Events: {p.get('upcoming_events', 'N/A')}",
        f"Social: {p.get('social_influence', 'N/A')}",
        f"TrendTool: {t}",
        f"SocialTool: {s}",
        f"EventTool: {ev}",
        f"RecommendationTool: {r}",
        f"FuturePurchaseTool: {n}",
        f"AlternativeFinderTool: {a}",
    ])

    # 4. Invoke LLM for formatting
    try:
        md = ChatOllama(model=MODEL_NAME, num_ctx=2048, temperature=0.1).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_text)]
        ).content
        
        # Validation check: Ensure the LLM didn't hallucinate a completely different format
        if "### Your Profile Summary" in md and "*Disclaimer" in md:
            return md
        else:
            logging.warning("LLM hallucinatted output format. Falling back to deterministic formatter.")
    except Exception as exc:
        logging.error("LLM invocation failed.", exc_info=exc)
        
    # 5. Return deterministic string if LLM fails
    return fb
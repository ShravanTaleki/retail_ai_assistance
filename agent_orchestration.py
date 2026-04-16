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
SYSTEM_PROMPT = """You are an elite Personalized Retail AI Assistant. You will receive a User Profile, Local Trends, and Candidate Pools for products.

YOUR MISSION:
1. Select 3-5 products from the Candidate Pool that best fit the user's budget, style, and context.
2. Select 1-2 Future Purchases and 1-2 Alternatives.
3. You MUST provide a 1-sentence personalized reasoning for EVERY item you select.
CRITICAL RULE: You must write ORIGINAL reasoning that makes logical sense for the SPECIFIC products you selected. Do not compare unrelated items and do not mention items you did not recommend.

CRITICAL ETHICS RULE: Keep your tone helpful but objective. Do NOT use manipulative sales tactics (e.g., "Buy now before it's gone!"), do NOT make guaranteed savings claims, and do NOT make discriminatory assumptions based on gender, race, or body type. Clearly label all recommendations as suggestions.

EXAMPLE OUTPUT FORMAT (Follow this structure exactly, including the exact ### headers):

### Your Profile Summary
- [Insert user age, interest, and budget]
- [Insert color and brand preferences]
- Location: [Insert location]
- Upcoming Event: [Insert event]

### Local Trend & Peer Insight
- [Insert trend insight from tools]
- [Insert peer insight from tools]

### Recommended for You
- **[Selected Product Name 1]**: [Write original reasoning explaining how this specific item fits the user's budget, favorite color, or preferred brand].
- **[Selected Product Name 2]**: [Write original reasoning explaining how this specific item connects to the local trends or upcoming events].
- **[Selected Product Name 3]**: [Write original reasoning explaining why this is a good fit].

### Next Likely Purchases
- **[Selected Future Product]**: [Write original reasoning explaining exactly how this item logically pairs with the specific products recommended above].

### Alternatives
- **[Alternative Product Name]**: [Write original reasoning explaining why this item is a great alternative to one of your recommendations based on being a different price tier or brand].
"""

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
        *_bullets(r)[:5],  # Fallback gracefully limits list
        "",
        "### Next Likely Purchases",
        *_bullets(n)[:3],
        "",
        "### Alternatives",
        *_bullets(a)[:3],
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
    
    # --- MISSING DATA SANITIZATION ---
    # Handle missing location
    loc = p.get("location", "")
    safe_loc = loc if loc and str(loc).strip() else "Not Specified / Online"
    p["location"] = safe_loc
    
    # Handle missing or invalid budget
    raw_budget = p.get("budget", 150)
    try:
        safe_budget = int(raw_budget) if raw_budget else 150
    except (ValueError, TypeError):
        safe_budget = 150
    p["budget"] = safe_budget
    # ---------------------------------

    t = get_local_trends.invoke({"location": safe_loc})
    s = (
        get_peer_purchases.invoke({"user_id": p.get("user_id", 0)})
        if p.get("user_id")
        else "Insight: Peer purchase signals are currently limited for new users."
    )
    ev = get_upcoming_events.invoke({"location": safe_loc})
    r = get_product_recommendations.invoke({
        "budget": safe_budget,
        "colors": p.get("favorite_colors", ""),
        "brand": p.get("brand_affinity", ""),
        "primary_interest": p.get("primary_interest", ""),
    })
    n = get_future_purchases.invoke({
        "budget": safe_budget,
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
        f"Candidate Product Pool: {r}",
        f"Candidate Future Purchases: {n}",
        f"Candidate Alternatives: {a}",
    ])

    # 4. Invoke LLM for formatting
    try:
        md = ChatOllama(model=MODEL_NAME, num_ctx=2048, temperature=0.1).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_text)]
        ).content
        
        # Validation check: Ensure the LLM generated the core headers
        if "### Your Profile Summary" in md:
            # Safely append the disclaimer in Python instead of relying on the LLM
            final_output = md.strip() + "\n\n*Disclaimer: Recommendations are based on synthetic demo data.*"
            return final_output
        else:
            logging.warning("LLM hallucinated output format. Falling back to deterministic formatter.")
    except Exception as exc:
        logging.error("LLM invocation failed.", exc_info=exc)
        
    # 5. Return deterministic string if LLM fails
    return fb
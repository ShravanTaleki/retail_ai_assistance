"""Linear agent orchestrator: gather data via Pandas tools → format via LLM (or deterministic fallback)."""
import re
import json
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
1. Select 5-6 products from the Candidate Pool that best fit the user's budget, style, and context.
2. Select 3-6 Future Purchases and 3-6 Alternatives.
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
- **[Selected Product Name 1]**: [Reasoning tied to budget or color preference].
- **[Selected Product Name 2]**: [Reasoning tied to local trends or upcoming events].
- **[Selected Product Name 3]**: [Reasoning tied to brand affinity].
- **[Selected Product Name 4]**: [Reasoning tied to past purchases or interest].
- **[Selected Product Name 5]**: [Reasoning tied to social signals].
- **[Selected Product Name 6]**: [Reasoning for any strong fit].

### Next Likely Purchases
- **[Future Product 1]**: [Reasoning: complements the recommended items above].
- **[Future Product 2]**: [Reasoning: complements the recommended items above].
- **[Future Product 3]**: [Reasoning: complements the recommended items above].

### Alternatives
- **[Alternative Product 1]**: [Reasoning: different brand or price tier than a recommendation].
- **[Alternative Product 2]**: [Reasoning: different brand or price tier than a recommendation].
- **[Alternative Product 3]**: [Reasoning: different brand or price tier than a recommendation].
"""

# ── Formatting helpers ────────────────────────────────────────────────────────
def _bullets(text: str) -> list[str]:
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip().startswith("- ")]
    if lines:
        return lines
    nums = [f"- {m.strip()}" for m in re.findall(r"\d+\.\s(.*?)(?=\s\d+\.|$)", str(text))]
    return nums or [f"- {str(text).split(':', 1)[-1].strip()}"]

def _inject_prices(md: str, price_map: dict) -> str:
    """Scan every bold product bullet and prepend the real price from the CSV lookup (case-insensitive)."""
    def _replacer(match):
        name = match.group(1).strip()
        separator = match.group(2)
        rest = match.group(3).strip()
        # Case-insensitive lookup: the LLM may alter capitalisation slightly
        # Also strip tags like "(premium alternative)" that the LLM copies from candidate lists
        clean_name = re.sub(r'\s*\(.*?\)\s*$', '', name).strip()
        price = price_map.get(clean_name.lower())
        if price and f"${price:.2f}" not in rest:
            return f"**{name}**{separator} ${price:.2f} — {rest}"
        return match.group(0)
    return re.sub(r'\*\*(.*?)\*\*(\s*:?\s*)(.*)', _replacer, md)

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

    # 2. Extract text from the structured JSON for the LLM and fallback
    try:
        r_data = json.loads(r)
        r_text = r_data.get("text", r)
        items = r_data.get("items", [])
    except json.JSONDecodeError:
        r_text = r
        items = []

    # Build a case-insensitive price lookup map from the full products CSV
    from data_loader import load_products
    all_products_df = load_products()
    price_map = {row.product.lower(): float(row.price) for row in all_products_df.itertuples(index=False)}

    # 3. Build the fallback in case the LLM fails or goes rogue (also inject prices)
    fb = _inject_prices(_fallback(p, t, s, ev, r_text, n, a), price_map)

    # 4. Construct the LLM payload
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
        f"Candidate Product Pool:\n{r_text}",
        f"Candidate Future Purchases:\n{n}",
        f"Candidate Alternatives:\n{a}",
    ])

    # 4. Invoke LLM for formatting
    try:
        md = ChatOllama(model=MODEL_NAME, num_ctx=2048, temperature=0.1).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_text)]
        ).content
        
        # Validation check: Ensure the LLM generated the core headers
        if "### Your Profile Summary" in md:
            # Inject real prices from CSV before storing in session state
            md = _inject_prices(md, price_map)
            # Safely append the disclaimer in Python instead of relying on the LLM
            final_output = md.strip() + "\n\n*Disclaimer: Recommendations are based on synthetic demo data.*"
            return final_output
        else:
            logging.warning("LLM hallucinated output format. Falling back to deterministic formatter.")
    except Exception as exc:
        logging.error("LLM invocation failed.", exc_info=exc)
        
    # 5. Return deterministic string if LLM fails
    return fb
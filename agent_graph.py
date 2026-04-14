from typing import TypedDict
import re
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from tools import get_alternatives, get_future_purchases, get_local_trends, get_peer_purchases, get_product_recommendations, get_user_profile, get_upcoming_events
from config import MODEL_NAME

class AgentState(TypedDict, total=False):
    user_id: int; profile: dict; trends: str; peers: str; events: str; rec_data: str; next_data: str; alt_data: str; fast_mode: bool; result: str

SYSTEM_PROMPT = """You are a formatting assistant. Your job is to take the EXACT text provided by the tools and place it into the correct sections. Do not mix the outputs. Do not write your own text.

CRITICAL RULES:
1. Put the RecommendationTool output ONLY under "Recommended for You".
2. Put the FuturePurchaseTool output ONLY under "Next Likely Purchases".
3. Put the AlternativeFinderTool output ONLY under "Alternatives".

OUTPUT TEMPLATE:
### Your Profile Summary
- [Age Group], [Gender/Style], \\$[Budget] budget
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

def _items(text: str):
    bullets = [ln.strip() for ln in str(text).splitlines() if ln.strip().startswith("- ")]
    if bullets:
        return bullets
    nums = [f"- {x.strip()}" for x in re.findall(r"\d+\.\s(.*?)(?=\s\d+\.|$)", str(text))]
    return nums or [f"- {str(text).split(':', 1)[-1].strip()}"]

def _fallback(p, t, s, e, r, n, a):
    return "\n".join([
        "### Your Profile Summary", 
        f"- {p.get('age_group', 'Adult')}, {p.get('gender', 'General')}, \\${p.get('budget', 'N/A')} budget", 
        f"- Prefers {p.get('favorite_colors', 'N/A')} and {p.get('brand_affinity', 'N/A')}", 
        f"- Location: {p.get('location', 'N/A')}",
        f"- Upcoming Event: {p.get('upcoming_events', 'None')}",
        "", 
        "### Local Trend & Peer Insight", 
        f"- {t}", 
        f"- {s}", 
        f"- {e}",
        "", 
        "### Recommended for You", 
        *_items(r), 
        "", 
        "### Next Likely Purchases", 
        *_items(n), 
        "", 
        "### Alternatives", 
        *_items(a), 
        "", 
        "*Disclaimer: Recommendations are based on synthetic demo data.*"
    ])

def gather(state: AgentState):
    # Check if we have the profile directly in the state or need to fetch by user_id
    p = get_user_profile.invoke({
        "user_id": state.get("user_id"), 
        "profile": state if "gender" in state else state.get("profile")
    })
    t = get_local_trends.invoke({"location": p.get("location", "")})
    s = get_peer_purchases.invoke({"user_id": p.get("user_id", 0)}) if p.get("user_id") else "Insight: Peer purchase signals are currently limited."
    e = get_upcoming_events.invoke({"location": p.get("location", "")})
    r = get_product_recommendations.invoke({
        "budget": int(p.get("budget", 150)), 
        "colors": p.get("favorite_colors", ""), 
        "brand": p.get("brand_affinity", ""),
        "gender": p.get("gender", "General")
    })
    n = get_future_purchases.invoke({"budget": int(p.get("budget", 150))})
    a = get_alternatives.invoke({"recommendations_data": r, "colors": p.get("favorite_colors", "")})
    return {"profile": p, "trends": t, "peers": s, "events": e, "rec_data": r, "next_data": n, "alt_data": a}

def recommend(state: AgentState):
    p = state["profile"]
    user = "\n".join([
        f"Age Group: {p.get('age_group', 'Adult')}",
        f"Gender/Style: {p.get('gender', 'General')}", 
        f"Budget: {p.get('budget', 'N/A')}", 
        f"Location: {p.get('location', 'N/A')}",
        f"Brand: {p.get('brand_affinity', 'N/A')}", 
        f"Colors: {p.get('favorite_colors', 'N/A')}", 
        f"TrendTool: {state['trends']}", 
        f"SocialTool: {state['peers']}", 
        f"EventTool: {state['events']}",
        f"Recommendations Data: {state['rec_data']}", 
        f"Next Purchases Data: {state['next_data']}", 
        f"Alternatives Data: {state['alt_data']}"
    ])
    if state.get("fast_mode", True):
        return {"result": _fallback(p, state["trends"], state["peers"], state["events"], state["rec_data"], state["next_data"], state["alt_data"])}
    md = ChatOllama(model=MODEL_NAME, num_ctx=2048, temperature=0.1).invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user)]).content
    return {"result": md if "### Your Profile Summary" in md and "*Disclaimer: Recommendations are based on synthetic demo data.*" in md else _fallback(p, state["trends"], state["peers"], state["events"], state["rec_data"], state["next_data"], state["alt_data"])}

graph = StateGraph(AgentState)
graph.add_node("gather", gather)
graph.add_node("recommend", recommend)
graph.add_edge(START, "gather")
graph.add_edge("gather", "recommend")
graph.add_edge("recommend", END)
agent = graph.compile()

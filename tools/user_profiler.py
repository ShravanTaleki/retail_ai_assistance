from typing import Dict, Any, Optional
from langchain_core.tools import tool
from data_loader import load_users, load_purchases, load_events, load_social


@tool
def get_user_profile(user_id: Optional[int] = None, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a comprehensive profile dict with all parameters."""
    if profile and "primary_interest" in profile:
        return profile

    if user_id is None:
        return {}

    # Load base user data
    df = load_users()
    user_row = df.loc[df.user_id == int(user_id)]
    if user_row.empty:
        return {}
    user = user_row.iloc[0].to_dict()

    # 7. Past Purchases
    purchases_df = load_purchases()
    user_purchases = purchases_df.loc[purchases_df.user_id == int(user_id)].tail(3)
    user["past_purchases"] = (
        ", ".join(user_purchases["product"].tolist())
        if not user_purchases.empty
        else "No recent purchases"
    )

    # 8. Upcoming Events
    events = load_events()
    loc_events = [e for e in events if e["location"].lower() == str(user.get("location", "")).lower()]
    user["upcoming_events"] = (
        ", ".join(f"{e['name']} ({e['date']})" for e in loc_events[:2])
        if loc_events
        else "No local events"
    )

    # 9. Social Influence
    social_df = load_social()
    peers = social_df.loc[social_df.user_id == int(user_id), "peer_id"].tolist()
    user["social_influence"] = (
        f"Connected to {len(peers)} active shoppers"
        if peers
        else "Limited social signals"
    )

    return user

import json
import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_user_profile(user_id: int | None = None, profile: dict | None = None):
    """Return a comprehensive profile dict with all 9 parameters."""
    if profile and "gender" in profile:
        # For new shoppers, ensure we have the default structure
        return profile
    
    # Load base user data
    df = pd.read_csv(DATA_DIR / "users.csv")
    user_row = df[df.user_id == int(user_id)]
    if user_row.empty:
        return {}
    user = user_row.iloc[0].to_dict()
    
    # 1-6 are already in 'user': Age, Gender, Location, Budget, Brand, Colors
    
    # 7. Past Purchases
    purchases_df = pd.read_csv(DATA_DIR / "past_purchases.csv")
    user_purchases = purchases_df[purchases_df.user_id == int(user_id)].tail(3)
    user["past_purchases"] = ", ".join(user_purchases["product"].tolist()) if not user_purchases.empty else "No recent purchases"
    
    # 8. Upcoming Events
    events = json.loads((DATA_DIR / "events.json").read_text(encoding="utf-8"))
    loc_events = [e for e in events if e["location"].lower() == user["location"].lower()]
    user["upcoming_events"] = ", ".join([f"{e['name']} ({e['date']})" for e in loc_events[:2]]) if loc_events else "No local events"
    
    # 9. Social Influence
    social_df = pd.read_csv(DATA_DIR / "social_networks.csv")
    peers = social_df[social_df.user_id == int(user_id)]["peer_id"].tolist()
    user["social_influence"] = f"Connected to {len(peers)} active shoppers" if peers else "Limited social signals"
    
    return user

import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_peer_purchases(user_id: int):
    """Return one natural-language peer insight."""
    net = pd.read_csv(DATA_DIR / "social_networks.csv")
    peers = net[net.user_id == int(user_id)]["peer_id"]
    buy = pd.read_csv(DATA_DIR / "past_purchases.csv")
    rows = buy[buy.user_id.isin(peers)]
    if rows.empty:
        return "Insight: Peer purchase signals are currently limited."
    top = rows["product"].value_counts().idxmax()
    return f"Insight: Your peers are frequently buying {top}."

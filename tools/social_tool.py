from langchain_core.tools import tool
from data_loader import load_social, load_purchases

@tool
def get_peer_purchases(user_id: int) -> str:
    """Return one natural-language peer insight."""
    net = load_social()
    peers = net[net.user_id == int(user_id)]["peer_id"]
    buy = load_purchases()
    rows = buy[buy.user_id.isin(peers)]
    if rows.empty:
        return "Insight: Peer purchase signals are currently limited."
    top = rows["product"].value_counts().idxmax()
    return f"Insight: Your peers are frequently buying {top}."

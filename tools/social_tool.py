from langchain_core.tools import tool
import pandas as pd
from data_loader import load_social, load_purchases, load_users

@tool
def get_peer_purchases(user_id: int) -> str:
    """Return one natural-language peer insight based on direct peers or similar profiles."""
    net = load_social()
    buy = load_purchases()
    users = load_users()
    
    # 1. Direct Peers
    direct_peers = net[net.user_id == int(user_id)]["peer_id"].tolist()
    
    # 2. Similar Profiles (Similarity Matching Rule)
    user_row = users[users.user_id == int(user_id)]
    if not user_row.empty:
        u_info = user_row.iloc[0]
        similar_users = users[
            (users.age_group == u_info.age_group) & 
            (users.primary_interest == u_info.primary_interest) & 
            (users.user_id != int(user_id))
        ]["user_id"].tolist()
    else:
        similar_users = []
        
    combined_influencers = list(set(direct_peers + similar_users))
    
    rows = buy[buy.user_id.isin(combined_influencers)]
    if rows.empty:
        return "Insight: Peer purchase signals are currently limited for your exact profile."
        
    top = rows["product"].value_counts().idxmax()
    return f"Insight: Shoppers with similar profiles or in your network frequently buy {top}."


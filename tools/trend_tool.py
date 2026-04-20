from langchain_core.tools import tool
import pandas as pd
from data_loader import load_purchases, load_users, load_products

@tool
def get_local_trends(location: str) -> str:
    """Return one natural-language trend insight based on aggregated local purchases."""
    purchases = load_purchases()
    users = load_users()
    products = load_products()

    # Join users to purchases to filter by location
    merged = purchases.merge(users[["user_id", "location"]], on="user_id", how="inner")
    
    # Filter by the requested location
    local_data = merged[merged["location"].str.lower() == str(location).lower()]
    
    if local_data.empty:
        return f"Insight: No strong local trend data was found for {location}."

    # Join with products to get color and category
    local_items = local_data.merge(products[["product_id", "category", "color"]], on="product_id", how="inner")
    
    if local_items.empty:
        return f"Insight: No strong local trend data was found for {location}."

    # Group by category and color
    grouped = local_items.groupby(["category", "color"]).size().reset_index(name="count")
    
    # Get top selling category + color
    top_trend = grouped.sort_values("count", ascending=False).iloc[0]
    category = str(top_trend["category"]).lower()
    color = str(top_trend["color"]).lower()
    
    return f"Insight: In {location}, {color} {category}s have been the top-selling items this season."


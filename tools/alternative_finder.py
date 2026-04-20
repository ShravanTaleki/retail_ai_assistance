import json
import pandas as pd
from langchain_core.tools import tool
from typing import List
from data_loader import load_products


@tool
def get_alternatives(recommendations_data: str, colors: str) -> str:
    """For each recommended product, find an alternative based on style, price, and brand."""
    df = load_products()
    prefs = {c.strip().lower() for c in str(colors).split(",") if c.strip()}
    pairs: List[str] = []

    rec_names = []
    try:
        data = json.loads(recommendations_data)
        if "items" in data:
            rec_names = [item.get("product") for item in data["items"]]
    except json.JSONDecodeError:
        pass

    for name in rec_names:
        if not name:
            continue
        rec = df.loc[df["product"] == name]
        if rec.empty:
            continue
        rec_row = rec.iloc[0]

        # Find alternatives: same category, different product
        alt_pool = df.loc[
            (df["category"] == rec_row["category"]) & (df["product"] != rec_row["product"])
        ].copy()
        if alt_pool.empty:
            continue

        # Score alternatives based on color match and brand difference
        # An alternative is often good if it offers a different brand or price point, but matches style (color).
        color_match = alt_pool["color"].str.lower().isin(prefs).astype(int) * 2
        brand_diff = (alt_pool["brand"] != rec_row["brand"]).astype(int) * 1
        
        alt_pool["_score"] = color_match + brand_diff
        
        # Sort by score desc, then price
        best_alt = alt_pool.sort_values(["_score", "price"], ascending=[False, True]).iloc[0]
        
        price_diff = best_alt['price'] - rec_row['price']
        price_str = "cheaper" if price_diff < 0 else "premium"
        pairs.append(f"- {best_alt['product']} ({best_alt['brand']}, {price_str} alternative)")

    return "\n".join(pairs[:15]) if pairs else "- No close alternatives found."

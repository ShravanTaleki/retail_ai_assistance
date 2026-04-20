import json
import pandas as pd
from langchain_core.tools import tool
from typing import List
from data_loader import load_products


@tool
def get_future_purchases(budget: int = 150, recommendations_data: str = "") -> str:
    """Suggest 2 complementary items from different categories than the ones already recommended."""
    df = load_products()
    budget = int(budget)

    # Parse already recommended categories
    already_cats = set()
    try:
        data = json.loads(recommendations_data)
        if "items" in data:
            already_cats = {item.get("category", "").lower() for item in data["items"]}
    except json.JSONDecodeError:
        pass  # Fallback to empty if not valid JSON

    # Candidate pool: within budget, from a NEW category
    pool = df.loc[df["price"] <= budget].copy()
    if already_cats:
        pool = pool.loc[~pool["category"].str.lower().isin(already_cats)]

    if pool.empty:
        return "- No additional items found within budget."

    # Pick up to 2 items from distinct categories (cheapest per category)
    pool = pool.drop_duplicates(subset="product")
    picks = pool.groupby("category", group_keys=False).apply(
        lambda grp: grp.nsmallest(1, "price")
    )
    picks = picks.head(10)

    return "\n".join(f"- {r.product}" for r in picks.itertuples())

import re
import pandas as pd
from langchain_core.tools import tool
from typing import List
from data_loader import load_products


def _parse_recommended_names(text: str) -> List[str]:
    """Extract product names from recommendation bullet strings."""
    return re.findall(r"-\s(.+?)\s\(match", text)


@tool
def get_future_purchases(budget: int = 150, recommendations_data: str = "") -> str:
    """Suggest 2 complementary items from different categories than the ones already recommended."""
    df = load_products()
    budget = int(budget)

    # Determine which categories were already recommended
    rec_names = _parse_recommended_names(recommendations_data)
    rec_rows = df.loc[df["product"].isin(rec_names)]
    already_cats = set(rec_rows["category"].str.lower()) if not rec_rows.empty else set()

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
    picks = picks.head(2)

    return "\n".join(f"- {r.product}" for r in picks.itertuples())

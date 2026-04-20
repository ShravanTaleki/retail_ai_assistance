import json
import pandas as pd
from typing import List, Dict, Any
from langchain_core.tools import tool
from data_loader import load_products


@tool
def get_product_recommendations(budget: int, colors: str, brand: str, primary_interest: str = "") -> str:
    """Return JSON string of up to 15 deduplicated product recommendations filtered by budget, interest, color & brand."""
    df = load_products()
    prefs = [c.strip().lower() for c in str(colors).split(",") if c.strip()]
    budget = int(budget)

    # 1. Budget gate
    pool = df.loc[df["price"] <= budget].copy()
    if pool.empty:
        return json.dumps({"text": "- No products found within your budget.", "items": []})

    # 2. Primary interest filter — boost matching category, but keep others as fallback
    interest = str(primary_interest).strip()
    interest_pool = pool.loc[pool["category"].str.lower() == interest.lower()] if interest else pd.DataFrame()

    # 3. Color + brand preference filter
    color_mask = pool["color"].str.lower().isin(prefs)
    brand_mask = pool["brand"].str.lower() == str(brand).strip().lower()
    filtered = pool.loc[color_mask | brand_mask].copy()
    if filtered.empty:
        return json.dumps({"text": "- No products found matching your color/brand preferences.", "items": []})

    # 4. Score: interest match + brand match + color match
    filtered["_score"] = (
        filtered["category"].str.lower().eq(interest.lower()).astype(int) * 3
        + brand_mask[filtered.index].astype(int) * 2
        + color_mask[filtered.index].astype(int)
    )

    # 5. Dedup + top 15
    filtered = filtered.drop_duplicates(subset="product")
    top = filtered.sort_values(["_score", "price"], ascending=[False, True]).head(15)

    # 6. Build structured output
    lines: List[str] = []
    items: List[Dict[str, Any]] = []
    for row in top.itertuples(index=False):
        c_hit = row.color.lower() in prefs
        b_hit = row.brand.lower() == str(brand).strip().lower()
        if c_hit and b_hit:
            tag = "(matches color & brand)"
        elif b_hit:
            tag = "(matches brand)"
        else:
            tag = "(matches color)"
        lines.append(f"- {row.product} {tag}")
        items.append({
            "product": row.product,
            "category": row.category,
            "brand": row.brand,
            "color": row.color,
            "price": float(row.price)
        })

    return json.dumps({
        "text": "\n".join(lines),
        "items": items
    })

import re
import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR


def _parse_recommended_names(text: str) -> list[str]:
    """Extract product names from recommendation bullets."""
    return re.findall(r"-\s(.+?)\s\(match", text)


@tool
def get_alternatives(recommendations_data: str, colors: str):
    """For each recommended product, find the cheapest same-category alternative in preferred colors."""
    df = pd.read_csv(DATA_DIR / "products.csv")
    prefs = {c.strip().lower() for c in str(colors).split(",") if c.strip()}
    pairs: list[str] = []

    for name in _parse_recommended_names(recommendations_data):
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

        # Prefer color-matched alternatives when available
        if prefs:
            color_match = alt_pool.loc[alt_pool["color"].str.lower().isin(prefs)]
            if not color_match.empty:
                alt_pool = color_match

        cheapest = alt_pool.sort_values("price").iloc[0]
        pairs.append(f"- {cheapest['product']} vs {rec_row['product']} (budget vs premium)")

    return "\n".join(pairs[:3]) if pairs else "- No close alternatives found."

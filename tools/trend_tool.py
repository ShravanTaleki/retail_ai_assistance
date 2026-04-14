import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_local_trends(location: str):
    """Return one natural-language trend insight."""
    df = pd.read_csv(DATA_DIR / "trends.csv")
    rows = df[df.location.str.lower() == location.lower()].sort_values("score", ascending=False).head(1)
    if rows.empty:
        return "Insight: No strong local trend data was found for your area."
    item = str(rows.iloc[0]["trend"]).replace("_", " ")
    return f"Insight: {item}s are the top sellers in your local area."

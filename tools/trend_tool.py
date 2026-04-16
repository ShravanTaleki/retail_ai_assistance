from langchain_core.tools import tool
from data_loader import load_trends

@tool
def get_local_trends(location: str) -> str:
    """Return one natural-language trend insight."""
    df = load_trends()
    rows = df[df.location.str.lower() == location.lower()].sort_values("score", ascending=False).head(1)
    if rows.empty:
        return "Insight: No strong local trend data was found for your area."
    item = str(rows.iloc[0]["trend"]).replace("_", " ")
    return f"Insight: {item}s are the top sellers in your local area."

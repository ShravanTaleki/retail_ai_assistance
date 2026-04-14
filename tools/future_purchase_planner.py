import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_future_purchases(budget: int = 150):
    """Return specific accessory items from products.csv under budget."""
    df = pd.read_csv(DATA_DIR / "products.csv")
    
    # Filter for accessories
    acc = df[df["category"].isin(["Bag", "Sneakers", "Jacket"])].copy()
    acc = acc[acc["price"] <= int(budget)]
    
    if acc.empty:
        return "- Minimal backpack\n- White sneakers"
        
    picks = acc.sample(min(2, len(acc)))
    bullets = [f"- {r.product}" for r in picks.itertuples()]
    
    return "\n".join(bullets)

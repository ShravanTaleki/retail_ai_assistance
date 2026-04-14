import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_product_recommendations(budget: int, colors: str, brand: str, gender: str = "General"):
    """Return filtered markdown recommendations with strict gender/style rules."""
    df = pd.read_csv(DATA_DIR / "products.csv")
    prefs = [c.strip().lower() for c in str(colors).split(",") if c.strip()]
    
    pool = df[df["price"] <= int(budget)].copy()
    
    # Strict Gender/Style Filter
    g = str(gender).lower()
    if any(x in g for x in ["male", "mens", "streetwear"]):
        pool = pool[~pool["category"].isin(["Dress", "Heels"])]
    elif any(x in g for x in ["female", "womens"]):
        # Keep all or apply specific female filters if needed
        pass

    pool = pool[pool["color"].str.lower().isin(prefs) | pool["brand"].str.lower().eq(str(brand).lower())]
    pool["score"] = pool["brand"].str.lower().eq(str(brand).lower()).astype(int) * 2 + pool["color"].str.lower().isin(prefs).astype(int)
    top = pool.sort_values(["score", "price"], ascending=[False, True]).head(3)
    
    if top.empty:
        return "- No exact matches found for your style and budget."
        
    items = []
    for r in top.itertuples(index=False):
        color_hit = r.color.lower() in prefs
        brand_hit = r.brand.lower() == str(brand).lower()
        if color_hit and brand_hit:
            why = "(matches color and brand preference)"
        elif brand_hit:
            why = "(matches brand preference)"
        else:
            why = "(matches color preference)"
        
        items.append(f"- {r.product} {why}")
        
    return "\n".join(items)

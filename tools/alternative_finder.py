import re
import pandas as pd
from langchain_core.tools import tool
from config import DATA_DIR

def _recs(text: str):
    return re.findall(r"-\s(.+?)\s\(", text)

@tool
def get_alternatives(recommendations_data: str, colors: str):
    """Return comparative alternatives in same category."""
    df = pd.read_csv(DATA_DIR / "products.csv")
    prefs = {c.strip().lower() for c in str(colors).split(",") if c.strip()}
    pairs = []
    
    for name in _recs(recommendations_data):
        rec = df[df["product"] == name].head(1)
        if rec.empty: continue
        rec = rec.iloc[0]
        
        alt = df[(df["category"] == rec["category"]) & (df["product"] != rec["product"])]
        if prefs:
            color_match = alt[alt["color"].str.lower().isin(prefs)]
            alt = color_match if not color_match.empty else alt
            
        if alt.empty: continue
        a = alt.sort_values("price").iloc[0]
        
        # Clean, concise comparison
        pairs.append(f"- {a['product']} vs {rec['product']} (budget vs premium comparison)")
        
    return "\n".join(pairs[:3]) if pairs else "- No close alternatives found."

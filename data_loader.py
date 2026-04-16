import json
import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from config import DATA_DIR

@st.cache_data
def load_users() -> pd.DataFrame:
    """Load users dataset from disk, cached in memory."""
    return pd.read_csv(DATA_DIR / "users.csv")

@st.cache_data
def load_products() -> pd.DataFrame:
    """Load products dataset from disk, cached in memory."""
    return pd.read_csv(DATA_DIR / "products.csv")

@st.cache_data
def load_purchases() -> pd.DataFrame:
    """Load past purchases dataset from disk, cached in memory."""
    return pd.read_csv(DATA_DIR / "past_purchases.csv")

@st.cache_data
def load_social() -> pd.DataFrame:
    """Load social network relationships from disk, cached in memory."""
    return pd.read_csv(DATA_DIR / "social_networks.csv")

@st.cache_data
def load_trends() -> pd.DataFrame:
    """Load local trends dataset from disk, cached in memory."""
    return pd.read_csv(DATA_DIR / "trends.csv")

@st.cache_data
def load_events() -> List[Dict[str, Any]]:
    """Load local events dataset from disk, cached in memory."""
    return json.loads((DATA_DIR / "events.json").read_text(encoding="utf-8"))

def clear_users_cache() -> None:
    """Clears the cached users DataFrame so new users become immediately available."""
    load_users.clear()

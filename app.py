import re
import pandas as pd
import streamlit as st
from agent_orchestration import run_agent
from config import DATA_DIR, MODEL_NAME

# ── Page Config (Compact & Wide) ──────────────────────────────────────────────
st.set_page_config(page_title="Retail AI Studio", layout="wide", page_icon="✨", initial_sidebar_state="expanded")

# ── Luxury Dashboard CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* 1. Base fonts and canvas width */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 1200px; }
header, footer { display: none !important; } /* Hide Streamlit Chrome */

/* 2. Premium Hero Header */
.dash-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 1px solid rgba(128,128,128,0.2);
    padding-bottom: 1rem; margin-bottom: 1.5rem;
}
.dash-title {
    font-size: 2rem; font-weight: 700; margin: 0; line-height: 1.2;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.dash-subtitle { color: var(--text-color); opacity: 0.6; font-size: 0.9rem; font-weight: 500; }

/* 3. Interactive Tab Styling */
.stTabs [data-baseweb="tab-list"] { gap: 30px; border-bottom: 1px solid rgba(128,128,128,0.1); }
.stTabs [data-baseweb="tab"] { height: 50px; font-weight: 600; letter-spacing: 0.5px; opacity: 0.7; }
.stTabs [aria-selected="true"] { opacity: 1; color: #a855f7 !important; border-bottom: 2px solid #a855f7 !important; }

/* 4. Luxury Cards */
.glass-card {
    background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1);
    border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;
}

/* 5. Button Polish */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white !important;
    border: none; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ── Helper: Markdown Parser for Tabs ──────────────────────────────────────────
def parse_agent_output(md_text):
    """Splits the raw markdown by '###' to feed into interactive UI tabs."""
    sections = {}
    parts = md_text.split("### ")
    for part in parts:
        if not part.strip(): continue
        lines = part.strip().split('\n')
        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()
        sections[title] = content
    return sections

# ── Data Guard ────────────────────────────────────────────────────────────────
if not (DATA_DIR / "users.csv").exists():
    st.error("System Error: Data missing. Run `generate_data.py`.")
    st.stop()
users = pd.read_csv(DATA_DIR / "users.csv")

# ── Sidebar: Control Panel ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👥 Shopper Management")
    st.markdown("---")
    
    # Updated to look like a "Create New User" flow
    is_new_user = st.toggle("➕ Create New Shopper", value=False)
    payload: dict = {}
    
    if is_new_user:
        p = {}
        new_name              = st.text_input("Shopper Name", "e.g., Jane Doe")
        p["age_group"]        = st.selectbox("Age Bracket", ["Teen (13-17)", "Young Adult (18-35)", "Adult (36-55)", "Senior (55+)"])
        p["primary_interest"] = st.selectbox("Primary Segment", ["Electronics", "Home & Kitchen", "Fitness", "Beauty", "Apparel"])
        p["location"]         = st.text_input("Geo-Location", "New York")
        p["budget"]           = st.slider("Max Budget ($)", 20, 500, 150)
        p["brand_affinity"]   = st.selectbox("Target Brand", sorted(users.brand_affinity.unique()))
        p["favorite_colors"]  = st.text_input("Color Vectors", "Black, Silver")
        payload["profile"] = p
        
        st.caption("Profile will be saved to the database on submission.")
    else:
        uid = st.selectbox("Select Existing Shopper", users.user_id.tolist(), format_func=lambda x: f"ID: {x} — {users.loc[users.user_id.eq(x), 'name'].iloc[0]}")
        payload["user_id"] = int(uid)

    st.markdown("---")
    submit = st.button("Generate Recommendations", use_container_width=True)

# ── Main Dashboard Layout ─────────────────────────────────────────────────────
# Top Header
st.markdown("""
    <div class="dash-header">
        <div>
            <div class="dash-title">Retail Intelligence Studio</div>
            <div class="dash-subtitle">Deterministic Recommendation Engine • Offline LLM Synthesis</div>
        </div>
        <div style="text-align: right;">
            <div class="dash-subtitle" style="color:#10b981;">● System Online</div>
            <div class="dash-subtitle" style="font-size: 0.75rem;">Engine: %s</div>
        </div>
    </div>
""" % MODEL_NAME, unsafe_allow_html=True)

# Main Area (No right-side telemetry column anymore)
if submit:
    # ── Persist new shopper to CSV if in create mode ────────────────────────
    if is_new_user:
        next_id = int(users["user_id"].max()) + 1
        # Derive a rough age from the selected age_group bracket
        age_map = {"Teen (13-17)": 15, "Young Adult (18-35)": 26, "Adult (36-55)": 45, "Senior (55+)": 62}
        new_row = pd.DataFrame([{
            "user_id":          next_id,
            "name":             new_name.strip() or f"Shopper {next_id}",
            "age":              age_map.get(p["age_group"], 30),
            "age_group":        p["age_group"],
            "primary_interest": p["primary_interest"],
            "location":         p["location"],
            "budget":           p["budget"],
            "brand_affinity":   p["brand_affinity"],
            "favorite_colors":  p["favorite_colors"],
        }])
        new_row.to_csv(DATA_DIR / "users.csv", mode="a", header=False, index=False)
        users = pd.concat([users, new_row], ignore_index=True)  # update in-memory
        st.toast("✅ New shopper profile saved to database!")

    with st.spinner("✨ Aggregating Pandas rules & executing LLM..."):
        try:
            raw_md = run_agent(user_id=payload.get("user_id"), custom_profile=payload.get("profile"))
            sections = parse_agent_output(raw_md)
        except Exception as exc:
            st.error(f"Runtime Exception: {exc}")
            st.stop()
    
    # Interactive Tabs (Reordered: Profile -> Recs -> Alts -> Future)
    t1, t2, t3, t4 = st.tabs([
        "👤 Profile & Context", 
        "🛍️ Recommendations", 
        "⚖️ Alternatives", 
        "🔮 Future Plan"
    ])
    
    with t1:
        c_prof, c_trend = st.columns(2)
        with c_prof:
            st.markdown("#### Shopper DNA")
            st.markdown(f'<div class="glass-card">\n\n{sections.get("Your Profile Summary", "Profile data missing.")}\n\n</div>', unsafe_allow_html=True)
        with c_trend:
            st.markdown("#### Market Context")
            st.markdown(f'<div class="glass-card">\n\n{sections.get("Local Trend & Peer Insight", "Context missing.")}\n\n</div>', unsafe_allow_html=True)

    with t2:
        st.markdown("#### Primary Recommendations")
        st.markdown(f'<div class="glass-card" style="border-left: 4px solid #a855f7;">\n\n{sections.get("Recommended for You", "No recommendations found.")}\n\n</div>', unsafe_allow_html=True)
        
    with t3:
        st.markdown("#### Budget vs Premium Comparisons")
        st.markdown(f'<div class="glass-card">\n\n{sections.get("Alternatives", "No alternatives found.")}\n\n</div>', unsafe_allow_html=True)
        
    with t4:
        st.markdown("#### Sequential Shopping Plan")
        st.info("These items logically pair with the primary recommendations based on category synergy.")
        st.markdown(f'<div class="glass-card">\n\n{sections.get("Next Likely Purchases", "No future plan generated.")}\n\n</div>', unsafe_allow_html=True)
            
else:
    # Idle State
    st.markdown('<div style="padding: 4rem 2rem; text-align: center; opacity: 0.5;">', unsafe_allow_html=True)
    st.markdown("### 📭 Workspace Ready")
    st.markdown("Select an existing shopper or create a new profile from the left panel, then click **Generate Recommendations**.")
    st.markdown('</div>', unsafe_allow_html=True)
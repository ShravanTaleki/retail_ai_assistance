import pandas as pd
import streamlit as st
from agent_graph import agent
from config import DATA_DIR, MODEL_NAME

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="RetailAI · Smart Recommendations", layout="wide", page_icon="🛒")

# ── Custom CSS — transforms Streamlit into a premium dashboard ────────────────
st.markdown("""
<style>
/* ── Hide default Streamlit chrome ─────────────────────────────────────── */
#MainMenu, header, footer {visibility: hidden;}
div[data-testid="stDecoration"] {display: none;}

/* ── Typography & spacing ──────────────────────────────────────────────── */
html, body, [class*="css"] {font-family: 'Inter', 'Segoe UI', sans-serif;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}

/* ── Sidebar styling ───────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);}
section[data-testid="stSidebar"] * {color: #e2e8f0 !important;}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: #94a3b8 !important; font-weight: 600;
}
section[data-testid="stSidebar"] hr {border-color: #334155;}

/* ── Primary CTA button ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white !important; border: none; border-radius: 12px;
    padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 700;
    letter-spacing: 0.02em; transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35);
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.5);
}

/* ── Result cards ──────────────────────────────────────────────────────── */
.result-card {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px;
    padding: 2rem 2.5rem; margin-top: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.hero-title {
    font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}
.hero-sub {
    color: #64748b; font-size: 1rem; margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Data guard ────────────────────────────────────────────────────────────────
if not (DATA_DIR / "users.csv").exists():
    st.error("⚠️  Data not found — run `uv run python generate_data.py` first.")
    st.stop()

users = pd.read_csv(DATA_DIR / "users.csv")

# ── Sidebar: Shopper Profile Panel ────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### 🛒 RetailAI")
    st.caption("Personalized Recommendation Engine")
    st.markdown("---")
    mode = st.toggle("✦  Create custom profile", value=False)
    payload: dict = {}
    if mode:
        profile = {}
        profile["age_group"]        = st.selectbox("Age Group", ["Teen (13-17)", "Young Adult (18-35)", "Adult (36-55)", "Senior (55+)"])
        profile["primary_interest"] = st.selectbox("Primary Interest", ["Electronics", "Home & Kitchen", "Fitness", "Beauty", "Apparel"])
        profile["location"]         = st.text_input("Location", "New York")
        profile["budget"]           = st.slider("Budget ($)", 20, 500, 150)
        profile["brand_affinity"]   = st.selectbox("Preferred Brand", sorted(users.brand_affinity.unique()))
        profile["favorite_colors"]  = st.text_input("Preferred Colors", "Black, Silver")
        profile["past_purchases"]   = st.text_input("Recent Purchases", "Headphones, Yoga Mat")
        profile["upcoming_events"]  = st.text_input("Upcoming Event", "Holiday Shopping")
        profile["social_influence"] = st.text_input("Social Signal", "Tech enthusiast community")
        payload["profile"] = profile
    else:
        uid = st.selectbox(
            "Select existing shopper",
            users.user_id.tolist(),
            format_func=lambda x: f"{x} — {users.loc[users.user_id.eq(x), 'name'].iloc[0]}",
        )
        payload["user_id"] = int(uid)

    st.markdown("---")
    submit = st.button("Generate Recommendations", type="primary", use_container_width=True)

# ── Main Stage ────────────────────────────────────────────────────────────────
if submit:
    with st.spinner("🔍  Analyzing profile, trends & peer signals …"):
        try:
            res = agent.invoke(payload)
        except Exception as exc:
            st.error(f"Engine error — {exc}")
            st.stop()
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown(res.get("result", "_No output — please retry._"))
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # Hero welcome section
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<p class="hero-title">Your Personal Shopping Intelligence</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hero-sub">'
            'AI-powered product recommendations across Electronics, Home, Fitness, Beauty & Apparel — '
            'fully offline, zero hallucinations.'
            '</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**Engine:** `{MODEL_NAME}` via Ollama &nbsp;·&nbsp; "
            f"**Architecture:** Pandas Rule-Engine + LLM Formatter &nbsp;·&nbsp; "
            f"**Data:** {len(users)} synthetic shoppers"
        )
    with c2:
        st.markdown("")
        cols = st.columns(3)
        cols[0].metric("Categories", "5")
        cols[1].metric("Products", "300")
        cols[2].metric("Brands", "10")
    st.info("👈  Configure a shopper profile in the sidebar, then press **Generate Recommendations**.")

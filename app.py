import pandas as pd
import streamlit as st
from agent_graph import agent
from config import DATA_DIR

st.set_page_config(page_title="Retail AI Agent", layout="wide")
st.title("Offline Personalized Retail AI Agent")
if not (DATA_DIR / "users.csv").exists():
    st.warning("Run `python generate_data.py` first.")
    st.stop()

users = pd.read_csv(DATA_DIR / "users.csv")
mode = st.sidebar.toggle("Use new shopper form", value=False)
payload = {}
if mode:
    st.sidebar.subheader("New Shopper Profile")
    payload["age_group"] = st.sidebar.selectbox("Age Group", ["Teen (13-17)", "Young Adult (18-35)", "Adult (36-55)", "Senior (55+)"])
    payload["gender"] = st.sidebar.selectbox("Gender/Style", ["Menswear", "Womenswear", "Unisex/Neutral"])
    payload["location"] = st.sidebar.selectbox("Location", sorted(users.location.unique()))
    payload["budget"] = st.sidebar.slider("Budget ($)", 50, 500, 150)
    payload["brand_affinity"] = st.sidebar.selectbox("Brand Affinity", sorted(users.brand_affinity.unique()))
    payload["favorite_colors"] = st.sidebar.text_input("Colors", "Black, Blue")
    payload["past_purchases"] = st.sidebar.text_input("Past Purchases", "Sneakers, Jeans")
    payload["upcoming_events"] = st.sidebar.text_input("Upcoming Event", "Summer Vacation")
    payload["social_influence"] = st.sidebar.text_input("Social Connection", "Active in Fashion Community")
else:
    uid = st.sidebar.selectbox("Select existing user", users.user_id.tolist(), format_func=lambda x: f"{x} - {users.loc[users.user_id.eq(x), 'name'].iloc[0]}")
    payload["user_id"] = int(uid)

fast_mode = st.sidebar.checkbox("Fast Mode (Skip LLM Polish)", value=False)
payload["fast_mode"] = fast_mode

if st.button("Generate Recommendations", type="primary"):
    with st.spinner("Reasoning locally with Ollama..."):
        # Ensure we pass the profile data and any control flags like fast_mode to the graph
        res = agent.invoke(payload)
    st.markdown(res["result"])
    st.caption("Fully offline demo using local synthetic data and Ollama.")

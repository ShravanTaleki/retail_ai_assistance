import re
import pandas as pd
import streamlit as st
from agent_orchestration import run_agent
import logging
from config import DATA_DIR, MODEL_NAME
from data_loader import load_users, clear_users_cache
from chat_agent import get_chat_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Page Config (Compact & Wide) ──────────────────────────────────────────────
st.set_page_config(page_title="Retail AI Shopper", layout="wide", page_icon="🛍️", initial_sidebar_state="expanded")

# ── E-Commerce Dashboard CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
/* 1. Base fonts and canvas width */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; }
.block-container { padding-top: 4rem !important; padding-bottom: 1rem !important; max-width: 1400px; }
h1 { padding-top: 25px !important; padding-bottom: 10px !important; line-height: 1.5 !important; overflow: visible !important; }
.stHeadingContainer { overflow: visible !important; }

/* 2. Sleek Storefront Header */
.store-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 2px solid rgba(128, 128, 128, 0.2);
    padding-bottom: 1rem; margin-bottom: 2rem;
}
.store-title {
    font-size: 2.5rem; font-weight: 800; margin: 0; line-height: 1.2;
    color: var(--primary-color);
}
.store-subtitle { color: var(--text-color); opacity: 0.7; font-size: 1rem; font-weight: 500; }

/* 3. Product Cards (Streamlit Container styling tweak) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.2);
    padding: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.15), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
}

/* Category Badge */
.category-badge {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1px;
    color: #888888;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}

/* Custom Product Typography */
.product-title {
    font-size: 1.35rem; 
    font-weight: 700; 
    color: var(--text-color);
    margin-bottom: 0.5rem;
}

.reasoning-container {
    border-left: 3px solid rgba(128, 128, 128, 0.3);
    padding-left: 1rem;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.product-reasoning {
    font-style: italic;
    color: var(--text-color);
    opacity: 0.75;
    font-size: 0.95rem;
    line-height: 1.5;
}
.product-price {
    font-size: 1.6rem;
    font-weight: 800;
    color: #2ecc71;
    margin-top: 0.25rem;
    margin-bottom: 0.5rem;
}

/* 4. Add to Cart Button */
.stButton > button {
    background-color: #0f172a; 
    color: #ffffff !important;
    border: none; border-radius: 8px; font-weight: 600; 
    text-transform: uppercase; letter-spacing: 0.5px;
    width: 100%;
    padding: 0.5rem 1rem;
    transition: background-color 0.2s ease;
}
.stButton > button:hover {
    background-color: #334155;
    color: #ffffff !important;
}

/* 5. Sidebar Context Box */
.sidebar-context-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #334155;
}
/* Ensure bullet points inside sidebar look clean */
.sidebar-context-box ul {
    padding-left: 1.2rem;
    margin-bottom: 0;
}

/* 6. Disclaimer Footer */
.disclaimer-footer {
    text-align: center;
    color: #9ca3af;
    font-size: 0.8rem;
    margin-top: 4rem;
    padding-top: 2rem;
    border-top: 1px solid #f3f4f6;
}
</style>
""", unsafe_allow_html=True)

# ── Helper: Markdown Parsers ──────────────────────────────────────────────────
def parse_agent_output(md_text):
    """Splits the raw markdown by headers to feed into sections."""
    sections = {}
    
    disclaimer = ""
    if "Disclaimer:" in md_text:
        idx = md_text.find("Disclaimer:")
        disclaimer = "*Disclaimer:" + md_text[idx + len("Disclaimer:"):].strip()
        
    parts = re.split(r"(?m)^#{2,4}\s+", md_text)
    
    for part in parts:
        if not part.strip(): continue
        lines = part.strip().split('\n')
        title = lines[0].strip().replace("*", "").replace(":", "")
        content = '\n'.join(lines[1:]).strip()
        
        if "Disclaimer:" in content:
            idx = content.find("Disclaimer:")
            if idx > 0 and content[idx-1] == "*":
                idx -= 1
            content = content[:idx].strip()
            
        # Normalize titles to ensure UI compatibility
        title_lower = title.lower()
        if "profile summary" in title_lower: title = "Your Profile Summary"
        elif "local trend" in title_lower or "peer insight" in title_lower: title = "Local Trend & Peer Insight"
        elif "recommend" in title_lower: title = "Recommended for You"
        elif "next" in title_lower or "future" in title_lower or "likely" in title_lower: title = "Next Likely Purchases"
        elif "alternative" in title_lower: title = "Alternatives"

        sections[title] = content
        
    return sections, disclaimer

def extract_price(text):
    """Extracts $ price from text or defaults to mock price."""
    import random
    match = re.search(r'\$(\d+(?:\.\d{2})?)', text)
    if match:
        return f"${match.group(1)}"
    return f"${random.randint(29, 199)}.99"

def parse_bullet(bullet_str):
    """Extracts Product Name and Reasoning from a bullet point."""
    import re
    # Try to grab what's in the bold tags
    match = re.search(r"\*\*(.*?)\*\*(?:\s*:)?\s*(.*)", bullet_str)
    if match:
        name = match.group(1).strip()
        reason = match.group(2).strip()
        return name, reason
    # Fallback if no bold tags are used: split on first colon
    if ":" in bullet_str:
        parts = bullet_str.lstrip("- ").split(":", 1)
        name = parts[0].replace("**", "").strip()
        reason = parts[1].strip()
        return name, reason
    return "Product", bullet_str.lstrip("- ")

def render_product_grid(markdown_section, section_key, cols=3):
    """Renders the AI bullet recommendations efficiently as a grid of product cards."""
    if not markdown_section or markdown_section == "No recommendations found.":
        st.info("No items found.")
        return
        
    # Split the markdown block into individual bullet lines
    lines = [line for line in markdown_section.split("\n") if line.strip().startswith("-")]
    
    for i in range(0, len(lines), cols):
        cols_obj = st.columns(cols)
        for j, col in enumerate(cols_obj):
            if i + j < len(lines):
                name, reason = parse_bullet(lines[i+j])
                with col:
                    # Streamlit Container acting as our Card
                    with st.container(border=True):
                        st.markdown(f'<div class="category-badge">[SUGGESTION]</div>', unsafe_allow_html=True)
                        price = extract_price(name + " " + reason)
                        st.markdown(f'<div class="product-price">{price}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="product-title">{name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="reasoning-container"><div class="product-reasoning">{reason}</div></div>', unsafe_allow_html=True)
                        st.button("Add to Cart 🛒", key=f"cart_{section_key}_{i}_{j}")


# ── Initialization ────────────────────────────────────────────────────────────
if not (DATA_DIR / "users.csv").exists():
    st.error("System Error: Data missing. Run `generate_data.py`.")
    st.stop()
users = load_users()

# ── Chat Session State Init ───────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_context" not in st.session_state:
    st.session_state.chat_context = ""
if "show_chat_btn" not in st.session_state:
    st.session_state.show_chat_btn = False
if "dashboard_generated" not in st.session_state:
    st.session_state.dashboard_generated = False
if "raw_md" not in st.session_state:
    st.session_state.raw_md = ""

# ── 💬 Chatbot Dialog Definition ─────────────────────────────────────────────
@st.dialog("🛍️ AI Shopping Assistant")
def chat_dialog():
    st.caption("Ask about the current shopper's recommendations. Off-topic questions will be redirected.")
    
    # Message container defined first so updates show immediately
    msg_container = st.container()
    
    # Streamlit chat_input works perfectly within dialogs without st.rerun() breaking state
    user_input = st.chat_input("Your question: e.g. Which item is the best value?")
    
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("Thinking..."):
            reply = get_chat_response(st.session_state.chat_messages, st.session_state.chat_context)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        
    # Render messages inside the container
    with msg_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


# ── Sidebar: Control Panel & Context ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👥 Shopper Management")
    st.markdown("---")
    
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
    submit = st.button("Generate AI Assistant", use_container_width=True)
    
    # Placeholder for Agent Context (filled remotely after generation)
    context_placeholder = st.empty()



# ── Main Dashboard Layout (Storefront) ────────────────────────────────────────
# Top Header
st.markdown("""
    <div class="store-header">
        <div>
            <div class="store-title">🛍️ RetailAI Personal Shopper</div>
            <div class="store-subtitle">Discover products tailored perfectly to your style and local trends.</div>
        </div>
        <div style="text-align: right;">
            <div class="store-subtitle" style="color:#10b981;">● Online</div>
            <div class="store-subtitle" style="font-size: 0.75rem;">Engine: %s</div>
        </div>
    </div>
""" % MODEL_NAME, unsafe_allow_html=True)

if submit:
    # ── Persist new shopper to CSV if in create mode ────────────────────────
    if is_new_user:
        next_id = int(users["user_id"].max()) + 1
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
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                new_row.to_csv(DATA_DIR / "users.csv", mode="a", header=False, index=False)
                clear_users_cache() 
                users = load_users()  
                st.toast("✅ New shopper profile saved to database!")
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    st.error("Cannot save profile: The users.csv file is currently open in another program (like Excel). Please close it and try again.")
                    st.stop()

    # ── Reset chat + enable floating button for the new session ─────────────
    st.session_state.chat_messages = []
    st.session_state.chat_context = ""
    st.session_state.show_chat_btn = False

    with st.spinner("✨ Analyzing profile and local trends..."):
        try:
            raw_md = run_agent(user_id=payload.get("user_id"), custom_profile=payload.get("profile"))
            # Store generation state
            st.session_state.raw_md = raw_md
            st.session_state.dashboard_generated = True
            
            # Store context for the chatbot and reveal the floating button
            st.session_state.chat_context = raw_md
            st.session_state.show_chat_btn = True
        except Exception as exc:
            st.error(f"Runtime Exception: {exc}")
            st.stop()

if st.session_state.get('dashboard_generated', False):
    sections, disclaimer = parse_agent_output(st.session_state.raw_md)
    
    # ── Render Context into the Sidebar Placeholder ─────────────────────────
    with context_placeholder.container():
        st.markdown("### 📋 My Account & Context")
        if "Your Profile Summary" in sections:
            st.markdown("#### Your Profile Summary")
            st.markdown(f'<div class="sidebar-context-box">\n\n{sections["Your Profile Summary"]}\n\n</div>', unsafe_allow_html=True)
        if "Local Trend & Peer Insight" in sections:
            st.markdown("#### Local Trend Insight")
            st.markdown(f'<div class="sidebar-context-box">\n\n{sections["Local Trend & Peer Insight"]}\n\n</div>', unsafe_allow_html=True)

    # ── Render Main Storefront (Interactive Grid) ───────────────────────────
    st.markdown("### Recommended for You:")
    render_product_grid(sections.get("Recommended for You", ""), "rec", cols=3)
    
    st.markdown("---")
    st.markdown("### Next Likely Purchases:")
    render_product_grid(sections.get("Next Likely Purchases", ""), "next", cols=2)
    
    st.markdown("---")
    st.markdown("### Alternatives:")
    render_product_grid(sections.get("Alternatives", ""), "alt", cols=2)
    
    # Render Bottom Disclaimer
    if disclaimer:
        st.markdown(f'<div class="disclaimer-footer">{disclaimer}</div>', unsafe_allow_html=True)
            
else:
    # Idle State
    st.markdown('<div style="padding: 4rem 2rem; text-align: center; opacity: 0.5;">', unsafe_allow_html=True)
    st.markdown("### 🛒 Welcome to the Storefront")
    st.markdown("Select an existing shopper or create a new profile from the left panel, then click **Generate AI Assistant**.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── 💬 Floating Chat Button (shown only after generation) ───────────────────────
if st.session_state.show_chat_btn:
    # Giving the button type="primary" guarantees it receives the kind="primary" 
    # attribute in the DOM, making it 100% reliably targetable via CSS anywhere on the page.
    if st.button("💬 Ask Assistant", type="primary", help="Ask AI Assistant"):
        chat_dialog()
        
    st.markdown("""
    <style>
    /* Target strictly the primary button to make it float */
    button[kind="primary"] {
        position: fixed !important;
        bottom: 2.5rem !important;
        right: 2.5rem !important;
        z-index: 9999 !important;
        border-radius: 50px !important; /* Pill shape */
        width: auto !important;
        height: auto !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #10b981, #0ea5e9) !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.5) !important;
        padding: 0.75rem 1.5rem !important;
        color: white !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 6px 25px rgba(16, 185, 129, 0.7) !important;
        background: linear-gradient(135deg, #059669, #0284c7) !important;
        color: white !important;
        border: none !important;
    }
    /* Ensure the text is properly displayed */
    button[kind="primary"] p {
        margin: 0 !important;
        padding: 0 !important;
        font-size: inherit !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)

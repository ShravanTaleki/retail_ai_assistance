# 🛍️ RetailAI: Project Blueprint

## 🎯 Overview
**RetailAI** is a production-grade, offline-first retail recommendation engine. It solves the problem of "LLM Hallucinations" by using a **Hybrid Deterministic-Generative Architecture**. 

- **Deterministic Layer**: Pandas-based rule engines (Tools) filter real inventory data based on hard constraints (budget, brand, category).
- **Generative Layer**: A local LLM (Ollama) acts as a high-fidelity formatting and reasoning layer, taking factual tool outputs and crafting a personalized human-like response.

The system covers 5 core retail categories: **Electronics, Home & Kitchen, Fitness, Beauty, and Apparel.**

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Agent Framework**: LangChain (Modular tools & logic)
- **Local Inference**: Ollama (Default: `qwen2.5:1.5b`)
- **Data Processing**: Pandas (for the "Zero Hallucination" rule engine)
- **Frontend**: Streamlit (Premium UI with custom CSS)
- **Package Manager**: `uv` (for fast, reproducible environments)

---

## 🏗️ Architecture & Logic Flow

1.  **Context Injection**: The user selects a profile or enters manual preferences in the Streamlit Sidebar.
2.  **Tool Orchestration (`agent_orchestration.py`)**: 
    - The system invokes a series of specialized tools (`tools/`) in sequence.
    - These tools query local CSV/JSON databases using Pandas.
3.  **Synthesis**:
    - Factual data (Products, Alternatives, Trends) is gathered into a structured prompt.
4.  **LLM Formatting**:
    - The LLM receives the **Exact Strings** from tools.
    - It enforces a strict Markdown template (Profile -> Trends -> Recommendations -> Future Sales -> Alternatives).
5.  **Parsing & Rendering (`app.py`)**:
    - The Streamlit app parses this Markdown by headers to distribute content into interactive tabs: **Profile & Context**, **Recommendations**, **Alternatives**, and **Future Plan**.
6.  **Deterministic Fallback**:
    - If the LLM output is malformed or the server is down, a hardcoded Python formatter (using regex for bullet points) ensures the user still sees the factual recommendations.

---

## 📂 Project Structure Map

### 🟢 Core Logic
- `agent_orchestration.py`: The central orchestrator. It executes the tools and manages the LLM call/fallback logic. It uses a `SYSTEM_PROMPT` to enforce "Zero Hallucination" behavior.
- `tools/`:
    - `user_profiler.py`: Generates the "Shopper DNA" (Age group, interests, budget, location, brand affinity, colors, and past purchases).
    - `product_recommender.py`: The heart of the engine. Matches products based on 9+ parameters.
    - `alternative_finder.py`: Finds budget-friendly alternatives to recommended items.
    - `future_purchase_planner.py`: Suggests cross-selling items based on current recommendations.
    - `trend_tool.py` / `social_tool.py` / `event_tool.py`: Adds contextual "Market Context" flavor (e.g., "Trending in your area").

### 🔵 Frontend & UI
- `app.py`: Streamlit-based dashboard. 
    - **Luxury UI**: Custom CSS for glassmorphism, gradient headers, and polished buttons.
    - **Session Persistence**: Appends new user profiles to `users.csv` in real-time.
    - **Markdown Parsing**: Splits the agent's response into logical UI components for better UX.

### 🟡 Data Layer
- `generate_data.py`: Synthetic data generator. Creates `users.csv`, `products.csv`, `purchases.csv`, and `events.json`.
- `data_loader.py`: Centralized utility for reading data into Pandas DataFrames.
- `config.py`: Global constants like `MODEL_NAME`.

---

## 📊 Data Schema
The system operates on four main entities stored in the `data/` directory (generated at runtime):
- **Users**: `user_id, age_group, primary_interest, budget, location, brand_affinity, favorite_colors`.
- **Products**: `product_id, category, sub_category, product, price, color, brand, stock_level`.
- **Purchases**: Historical links between Users and Products.
- **Events/Trends**: Mock JSON data mapped to locations.

---

## 🚀 Key Operational Commands

### 1. Initialize System
```bash
# Generate synthetic database
uv run python generate_data.py
```

### 2. Pull Local Model
```bash
ollama pull qwen2.5:1.5b
```

### 3. Launch UI
```bash
uv run streamlit run app.py
```

---

## 🧠 LLM Interaction Protocol
When interacting with this codebase:
1.  **Maintain Logic/LLM Separation**: Never move product filtering logic into the LLM prompt. Keep it in the Python tools.
2.  **Strict Output**: The LLM should only be used for formatting and "conversationalizing" factual data.
3.  **Tool-First**: If adding a new feature (e.g., "Discount Finder"), create a new file in `tools/` and register it in `agent_orchestration.py`.

# 🛍️ RetailAI: Offline Personalized AI Agent

**RetailAI** is a production-ready, general retail recommendation assistant. It combines the deterministic reliability of **Pandas Rule-Engines** with the conversational power of **Local LLMs (via LangGraph and Ollama)**.

The system is designed to provide hyper-personalized insights across 5 core retail categories: **Electronics, Home & Kitchen, Fitness, Beauty, and Apparel.**

---

## 🏗️ The "Zero Hallucination" Architecture

Unlike traditional AI agents that might "guess" product inventory, RetailAI uses a **Hybrid Rule + LLM** approach:
1.  **Pandas Engine**: Filters real inventory data based on user budget, category, and brand preferences.
2.  **Logic Logic**: Deduplicates items and calculates affinity scores.
3.  **LLM Layer**: Takes the *factual* results from the tools and formats them into a premium Markdown experience.

**Result**: 100% accurate product data with 100% conversational engagement.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: [Download here](https://ollama.com/)
- **uv**: Fast Python package manager.

### 2. Setup Models
Ensure Ollama is running and pull the default model:
```bash
ollama pull qwen2.5:1.5b
```

### 3. Installation
Clone the repository and install dependencies using `uv`:
```bash
uv pip install -r requirements.txt
```

### 4. Data Generation
Generate the synthetic general-retail datasets (CSVs and JSON):
```bash
uv run python generate_data.py
```

### 5. Launch the Dashboard
Run the premium Streamlit UI:
```bash
uv run streamlit run app.py
```

---

## 📂 Project Structure

- `app.py`: Premium Dashboard UI with custom CSS and dashboard metrics.
- `agent_graph.py`: LangGraph orchestrator defining the data flow from "Gather" to "Recommend".
- `tools/`: Modular rule engines for profile analysis, product matching, and planning.
- `data/`: Local database storage for synthetic products, users, and trends.
- `architecture.md`: In-depth developer blueprint with execution flowcharts.
- `problem.md`: Project requirements and core functional scope.

---

## 🛠️ Key Features
- **9-Parameter Profiling**: Custom profiles including Brand Affinity, Social Influence, and Budget.
- **Contextual Planning**: Suggests logical follow-up purchases (cross-selling).
- **Comparative Analysis**: Automatically finds budget-friendly alternatives to premium items.
- **Robust Fallbacks**: Deterministic output generation if the AI model is offline or malformed.

---
*Disclaimer: This is a demo application using synthetic data for architectural demonstration.*

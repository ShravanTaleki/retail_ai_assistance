# Architecture: Offline Personalized Retail AI Agent

This document provides a comprehensive blueprint of the system's hybrid **"Rule + LLM"** architecture. It is designed to be self-explanatory for both human developers and AI models.

## 1. Core Philosophy: Hybrid Rule + LLM
The system is built on a "Logic first, Language second" principle:
- **Pandas Rule-Engine**: Handles 100% of the deterministic logic. This includes filtering by budget, matching colors, boosting brand affinity, and deduplicating products. Because Pandas is code-based, it ensures **0% hallucination** of product names or prices.
- **LangGraph Orchestrator**: Manages the state and flow of data between tools and the LLM.
- **LLM (Ollama)**: Acts strictly as a **Formatting Layer**. It receives the raw data from the tools and translates it into a premium, conversational Markdown report. It is explicitly instructed never to invent new products.

## 2. System Flowchart (LangGraph Logic)
Below is the execution graph of the agent:

```text
          +-----------+
          | __start__ |
          +-----------+
                |
                v
          +-----------+
          |  gather   |  <-- Invokes 7 Deterministic Tools (Pandas/JSON)
          +-----------+
                |
                v
          +-----------+
          | recommend |  <-- LLM Formatting Node (System Prompt Guard)
          +-----------+
                |
                v
          +-----------+
          |  __end__  |
          +-----------+
```

## 3. Directory Structure & Components
```text
retail_ai_assistance-main/
├── app.py                     # Premium Streamlit UI (Custom CSS)
├── agent_graph.py             # LangGraph State & Node Definitions
├── config.py                  # Global Constants (Model Name, Paths)
├── generate_data.py           # General Retail Synthetic Data Generator
├── problem.md                 # Requirements & Goals
├── architecture.md            # [This Document]
├── data/                      # Offline CSV/JSON Datasets
└── tools/                     # Modular Rule Engines
    ├── user_profiler.py       # Aggregates 9 profile parameters
    ├── product_recommender.py # Core filtering & scoring logic
    ├── future_purchase_planner.py # Contextual cross-selling logic
    ├── alternative_finder.py  # Price-based comparative logic
    ├── trend_tool.py          # Location-based popularity lookup
    ├── social_tool.py         # Peer-based recommendation signals
    └── event_tool.py          # Local event context lookup
```

## 4. The 9-Parameter Personalization Stack
The system tracks and utilizes 9 specific parameters to ensure "Hyper-Personalization":
1. **Age Group**: Used for demographic tailoring.
2. **Primary Interest**: (e.g., Electronics, Fitness) Used as the primary filter for recommendations.
3. **Location**: Used for local trends and event lookup.
4. **Budget**: Strict numerical ceiling for all product tools.
5. **Brand Affinity**: Boosts scores for preferred brands in the rule engine.
6. **Favorite Colors**: Boosts scores for preferred item finishes.
7. **Past Purchases**: Used for peer-similarity and future planning.
8. **Upcoming Events**: Injects occasion-aware context (e.g., "Ready for Summer Sale").
9. **Social Influence**: Connects peer buying patterns to user suggestions.

## 5. Tool Chain Logic
- **`product_recommender.py`**: Filters `products.csv`. It assigns a score based on Brand (+2) and Color (+1). It deduplicates items by name and returns the top 3 within budget.
- **`future_purchase_planner.py`**: Analyzes what was recommended and picks complementary items from **different** categories to suggest a logical next purchase.
- **`alternative_finder.py`**: Parses the recommended items and finds the cheapest possible alternative in the same category for "Budget vs Premium" comparisons.

## 6. Resilience & Fallbacks
The system is built for production robustness:
- **Empty State Handling**: Every Pandas tool checks if a filter returns an empty dataframe. If so, it returns a graceful "No items found" string instead of crashing.
- **LLM Guard**: `agent_graph.py` contains a `_fallback()` function. If the LLM output is malformed or the Ollama server is unreachable, the system automatically generates a deterministic Markdown report, ensuring 100% uptime.

---
*Blueprint Version: 2.0 (General Retail Expansion)*

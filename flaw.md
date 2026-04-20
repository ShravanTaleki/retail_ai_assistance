# Project Architectural Review (Sprint 2): Advanced Performance & Architecture

This document identifies expert-level architectural flaws, state management issues, and bottlenecks currently present in the Retail AI Assistant.

---

## 1. Architectural Design Flaws

### **[CRITICAL] LLM Role Misallocation (Formatter vs. Reasoner)**
- **File**: `agent_orchestration.py`, `app.py`
- **Flaw**: The LLM is currently serving as a Markdown Layout Formatter. It is forced to regenerate static data (product names, headers, prices) and wrap it all in a strict schema.
- **Impact**: This heavily bloats the output tokens, drastically increasing Time-To-First-Token (TTFT) and total generation time (resulting in the ~1 minute delays on 1.5b models). Small LLMs frequently hallucinate markdown headers, enforcing brittle parsing loops in the UI layer.
- **Expert Fix**: Decouple layout from reasoning. The LLM should only iterate through the candidate JSON payload and generate `<reason>...</reason>` tags. The Streamlit UI should construct the components using the JSON datastore natively, injecting the LLM reasoning dynamically.

---

## 2. Execution Bottlenecks

### **Synchronous Tool Aggregation**
- **File**: `agent_orchestration.py`
- **Flaw**: The orchestration layer executes `get_user_profile()`, `get_local_trends()`, `get_peer_purchases()`, and `get_upcoming_events()` sequentially using standard blocking Python operations.
- **Impact**: Cumulative delay. Each pandas lookup blocks the event loop, stacking up time before the LLM is even invoked.
- **Expert Fix**: Implement a `concurrent.futures.ThreadPoolExecutor` to run independent offline data-gathering tools in parallel.

---

## 3. Data & State Management

### **Infinite Cache Persistence**
- **File**: `data_loader.py`
- **Flaw**: The application leverages `@st.cache_data` for all CSV/JSON loads (`products`, `trends`, `past_purchases`, `events`). The cache is never invalidated (except `users.csv` upon creation).
- **Impact**: In a real-world edge environment, caching transactional or trending data indefinitely leads to staleness. New purchases or sudden shifts in social metrics will not be visible unless the underlying Streamlit server reboots.
- **Expert Fix**: Assign a Time-To-Live (TTL) constraint directly on the decorator (e.g., `@st.cache_data(ttl=300)`) for high-velocity datasets to force a background refresh on interval.

---

## 4. Analytical Precision Constraints

### **Static Horizon Look-aheads**
- **File**: `tools/event_tool.py`
- **Flaw**: The `get_upcoming_events` function scans exactly 30 days ahead for every single profile variant.
- **Impact**: This rigid look-ahead window works for immediate purchases (e.g., Apparel) but fails for longer-horizon retail trends (e.g., Home & Kitchen or high-ticket Electronics, where seasonal planning begins 60-90 days in advance).
- **Expert Fix**: Introduce dynamic horizon scanning based on the derived `primary_interest` of the user profile. (Apparel = 30-day look-ahead, Electronics/Kitchen = 60-90 day look-ahead).

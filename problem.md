# Offline Personalized Retail AI Agent

## 1. Project Overview & Goal
Modern retail customers expect highly personalized recommendations that consider their profile, local trends, social/peer influence, upcoming events, and smart planning. Traditional rule-based recommenders lack contextual understanding and explainability.

**Goal**: Build an offline AI recommendation assistant that:
- Generates personalized product recommendations based on a shopper profile.
- Explains recommendations with contextual reasoning.
- Adapts recommendations using local trends, social/peer influence, and upcoming events.
- Plans the next 2-3 likely purchases.
- Performs comparative suggestions across style, price, and brand.

## 2. Intended Users
- Online retail shoppers (demo persona)
- Retail merchandising teams
- Marketing and personalization teams
- AI / IT learning audience

## 3. Scope Definition
**In Scope:**
- Mock shopper profiles and synthetic purchase history
- Rule + LLM reasoning architecture
- Offline recommender logic with conversational explanations

**Out of Scope:**
- Live e-commerce platforms and real payment systems
- Behavioral tracking or real customer data
- Real competitor scraping

## 4. Functional Requirements
- **Local Trends Insight**: The agent must answer what is popular based on an area using a local sales dataset.
- **Social / Network-Based Recommendations**: Consider what friends/peers are buying using a mock "connections" dataset and similarity rules.
- **Event & Occasion-Aware**: Adjust recommendations based on a static event calendar.
- **Personalized Product Recommendation Engine**: Recommend 3-5 products per interaction with clear, personalized reasoning considering profile fit, popularity, occasion, and budget.
- **Purchase Planning**: Proactively suggest the next likely 2-3 purchases and logical shopping sequences.
- **Comparative Recommendations**: Provide alternative options comparing style, price range, and brand value based on a synthetic catalog.

## 5. Non-Functional Requirements
- Runs completely offline using Ollama LLMs (e.g., llama3, qwen)
- Handles missing data gracefully
- Delivers responses in < 5 seconds
- Provide easy-to-understand outputs (Profile, Insights, Recommendations, Plans, Alternatives, Disclaimer)
- Tech Stack: Python, Streamlit, Pandas, LangChain/LangGraph

## 6. Ethics & Safety
- Avoid manipulation, discriminatory profiling, or guaranteed savings claims.
- Clearly label recommendations as suggestions.

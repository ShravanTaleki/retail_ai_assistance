# Retail AI Assistance

A high-end, conversational retail assistant powered by local AI (Ollama) and LangGraph. This agent provides personalized product recommendations based on user profiles, local trends, peer social signals, and budget constraints.

## Features

-   **Conversational Polish**: Rewrites robotic tool output into natural, helpful language.
-   **Fully Offline**: Runs entirely on your local machine using Ollama and synthetic data.
-   **Robust UI**: Built with Streamlit, featuring escaped LaTeX math rendering to prevent text corruption.
-   **Data-Driven**: Uses local CSV/JSON data for user profiles, trends, and product catalogs.

## Tech Stack

-   **Logic**: Python, LangChain, LangGraph
-   **Model**: Ollama (`llama3.2:3b`)
-   **Interface**: Streamlit
-   **Data**: Pandas, Faker
-   **Environment**: `uv` for package management

## Getting Started

### Prerequisites

1.  **Ollama**: Ensure Ollama is installed and running.
    ```bash
    ollama pull llama3.2:3b
    ```
2.  **uv**: Install the `uv` tool for fast Python project management.

### Installation & Setup

1.  Initialize the project and install dependencies:
    ```bash
    uv init
    uv add -r requirements.txt
    ```

2.  Generate synthetic retail data:
    ```bash
    uv run .\generate_data.py
    ```

3.  Launch the application:
    ```bash
    uv run streamlit run app.py
    ```

## Project Structure

-   `app.py`: Streamlit frontend.
-   `agent_graph.py`: LangGraph orchestrator and System Prompt logic.
-   `tools/`: Modular Python tools for data retrieval (recommender, trends, social, etc.).
-   `config.py`: Path and environment configuration.
-   `generate_data.py`: Script to populate local CSV/JSON files.

---
*Disclaimer: This is a demo application using synthetic data.*

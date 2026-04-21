"""Retail-only chatbot logic. Isolated from the main recommendation engine."""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from config import MODEL_NAME

_CHAT_SYSTEM_PROMPT = """You are a helpful Retail Shopping Assistant embedded inside the RetailAI Personal Shopper application.

You have been given a Shopper's profile and their current product recommendations as context.

YOUR STRICT RULES:
1. You may ONLY answer questions related to: the shopper's profile, the recommended products, alternatives, future purchases, local trends, pricing, or general shopping advice.
2. If a user asks ANYTHING outside of this retail context (e.g., general knowledge, coding, history, science, creative writing), you must politely decline and redirect them. Example: "I'm a retail assistant and can only help with shopping-related questions for this shopper!"
3. Do NOT invent product names, prices, or facts not present in the context.
4. Keep answers concise — 2-4 sentences max.

SHOPPER CONTEXT:
{shopper_context}
"""


def get_chat_response(messages: list[dict], shopper_dna: str) -> str:
    """
    Takes the full chat history and the current shopper context,
    returns a string response from the LLM.

    Args:
        messages: List of dicts with 'role' ('user'/'assistant') and 'content'.
        shopper_dna: A string summary of the active shopper's profile and recommendations.

    Returns:
        A string response from the LLM.
    """
    system_prompt = _CHAT_SYSTEM_PROMPT.format(shopper_context=shopper_dna)

    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    try:
        response = ChatOllama(model=MODEL_NAME, num_ctx=2048, temperature=0.3).invoke(lc_messages)
        return response.content.strip()
    except Exception as exc:
        return f"⚠️ Could not reach the AI model. Please ensure Ollama is running. (Error: {exc})"

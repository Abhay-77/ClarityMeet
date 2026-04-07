import ollama
from .store_search_db import get_rag_context_for_meeting

def generate_meeting_minutes(meeting_id: str):
    # Pull decisions + action items + relevant transcript chunks
    # Use the same RAG context you already built for the chatbot
    context = get_rag_context_for_meeting(meeting_id)

    prompt = f"""
    Generate professional, concise meeting minutes using the context below.
    Use clear headings and bullet points.
    Keep it short and actionable.

    Context:
    {context}
    """

    response = ollama.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]
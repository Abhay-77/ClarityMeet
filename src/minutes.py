import os
from dotenv import load_dotenv
from src.cloudflare_ai import chat
from src.store_search_db import get_rag_context_for_meeting

load_dotenv()
CF_CHAT_MODEL = os.getenv("CF_CHAT_MODEL", "@cf/meta/llama-3-8b-instruct")

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

    response_text = chat(
        [{"role": "user", "content": prompt}],
        CF_CHAT_MODEL,
    )

    return response_text
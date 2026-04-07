from supabase import create_client, Client
from datetime import date
from dotenv import load_dotenv
import os
from src.cloudflare_ai import chat, embed

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CF_CHAT_MODEL = os.getenv("CF_CHAT_MODEL", "@cf/meta/llama-3-8b-instruct")
CF_EMBED_MODEL = os.getenv("CF_EMBED_MODEL", "@cf/baai/bge-large-en-v1.5")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using Cloudflare Workers AI."""
    return embed(text, CF_EMBED_MODEL)

def save_transcript_and_extracted(
    meeting_id: str,
    filename: str,
    transcript_entries: list,      # list of {"timestamp", "speaker", "content"}
    extracted_list: list,          # your extracted decisions/action items
    original_file_bytes: bytes = None
):
    # Optional: Upload original file to storage
    # if original_file_bytes:
    #     supabase.storage.from_("transcripts").upload(
    #         path=f"{meeting_id}/{filename}",
    #         file=original_file_bytes,
    #         file_options={"content-type": "text/plain"}
    #     )

    # 1. Save structured decisions & action items
    for item in extracted_list:
        data = {
            "type": item["type"],
            "content": item.get("decision") or item.get("action_item"),
            "who": item.get("who", ""),
            "when": item.get("when", ""),
            "timestamp": item.get("timestamp", ""),
            "speaker": item.get("speaker", "")
        }
        supabase.table("extracted_items").insert({
            "meeting_id": meeting_id,
            "filename": filename,
            "meeting_date": str(date.today()),
            "item_type": item["type"],
            "data": data
        }).execute()

    # 2. Save transcript chunks WITH embeddings
    CHUNK_SIZE = 8
    for i in range(0, len(transcript_entries), CHUNK_SIZE):
        chunk = transcript_entries[i:i + CHUNK_SIZE]
        chunk_text = "\n".join(
            f"{e['timestamp']} | {e['speaker']} | {e['content']}" for e in chunk
        )
        
        # Generate embedding
        embedding = generate_embedding(chunk_text)

        supabase.table("transcript_chunks").insert({
            "meeting_id": meeting_id,
            "filename": filename,
            "chunk_index": i // CHUNK_SIZE,
            "content": chunk_text,
            "timestamp_start": chunk[0]["timestamp"],
            "timestamp_end": chunk[-1]["timestamp"],
            "embedding": embedding
        }).execute()

    print(f"✅ Saved {len(extracted_list)} items + {len(transcript_entries)//CHUNK_SIZE} embedded chunks for {filename}")

def ask_meeting_intelligence(question: str, top_k: int = 10):
    # Generate embedding for the user question
    question_embedding = generate_embedding(question)

    context_parts = []
    citations = []

    # 1. Semantic search on transcript chunks (best for "why" questions)
    chunks_resp = supabase.rpc("match_chunks", {
        "query_embedding": question_embedding,
        "match_threshold": 0.75,
        "match_count": top_k
    }).execute()

    for row in chunks_resp.data:
        context_parts.append(
            f"Conversation from {row['meeting_id']} at {row['timestamp_start']}:\n{row['content']}"
        )
        citations.append(f"• {row['meeting_id']} – {row['filename']} – {row['timestamp_start']}")

    # 2. Also pull structured decisions/action items (fast exact matches)
    extracted_resp = supabase.table("extracted_items") \
        .select("meeting_id, filename, data") \
        .limit(top_k).execute()

    for row in extracted_resp.data:
        d = row["data"]
        if d["type"] == "decision":
            context_parts.append(f"Decision from {row['meeting_id']}: {d['content']}")
        else:
            context_parts.append(f"Action by {d.get('who')} from {row['meeting_id']}: {d['content']} (due {d.get('when')})")

    context = "\n\n".join(context_parts)

    system_prompt = f"""
    You are the Meeting Intelligence Hub assistant.
    Answer using ONLY the provided context.
    For "why" questions, use the conversation chunks to explain the reasoning behind decisions.
    Always cite the meeting and timestamp when possible.
    If you cannot find the answer, say "I couldn't find that information in any uploaded meeting."

    Context:
    {context}
    """

    # Call Ollama
    response_text = chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        CF_CHAT_MODEL,
    )
    return response_text or "Sorry, I couldn't generate an answer at this time."


def get_rag_context_for_meeting(meeting_id: str, max_chunks: int = 40):
    chunks_resp = supabase.table("transcript_chunks") \
        .select("meeting_id, filename, content, timestamp_start, chunk_index") \
        .eq("meeting_id", meeting_id) \
        .execute()

    extracted_resp = supabase.table("extracted_items") \
        .select("meeting_id, filename, data") \
        .eq("meeting_id", meeting_id) \
        .execute()

    chunks = sorted(chunks_resp.data or [], key=lambda row: row.get("chunk_index", 0))
    chunks = chunks[:max_chunks]
    extracted = extracted_resp.data or []

    context_parts = []

    for row in extracted:
        d = row["data"]
        if d["type"] == "decision":
            context_parts.append(f"Decision: {d['content']}")
        else:
            context_parts.append(
                f"Action: {d.get('who')} - {d['content']} (due {d.get('when')})"
            )

    for row in chunks:
        context_parts.append(
            f"Conversation at {row['timestamp_start']}:\n{row['content']}"
        )

    return "\n\n".join(context_parts)
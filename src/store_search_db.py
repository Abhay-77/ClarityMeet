from supabase import create_client, Client
import ollama
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_transcript_and_extracted(
    meeting_id: str,
    filename: str,
    transcript_entries: list,          # your list of {"timestamp", "speaker", "content"}
    extracted_list: list,              # your extracted decisions/action items
    original_file_bytes: bytes = None
):
    # 1. Optional: Store original file in Supabase Storage
    # if original_file_bytes:
    #     supabase.storage.from_("transcripts").upload(
    #         path=f"{meeting_id}/{filename}",
    #         file=original_file_bytes
    #     )

    # 2. Save extracted items (structured)
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

    # 3. Save chunked transcript (this gives us the "why" context)
    CHUNK_SIZE = 8   # ~8 lines per chunk (adjust as needed)
    for i in range(0, len(transcript_entries), CHUNK_SIZE):
        chunk = transcript_entries[i:i+CHUNK_SIZE]
        chunk_text = "\n".join(
            f"{e['timestamp']} | {e['speaker']} | {e['content']}" for e in chunk
        )
        supabase.table("transcript_chunks").insert({
            "meeting_id": meeting_id,
            "filename": filename,
            "chunk_index": i // CHUNK_SIZE,
            "content": chunk_text,
            "timestamp_start": chunk[0]["timestamp"],
            "timestamp_end": chunk[-1]["timestamp"]
        }).execute()

    print(f"✅ Saved {len(extracted_list)} extracted items + {len(transcript_entries)//CHUNK_SIZE} transcript chunks")

def ask_meeting_intelligence(question: str, top_k: int = 8):
    # Hybrid retrieval: structured items + transcript chunks
    # First get relevant decisions/actions
    extracted_resp = supabase.table("extracted_items") \
        .select("meeting_id, filename, data") \
        .or_(f"data->>content.ilike.%{question}%") \
        .execute()

    # Then get relevant conversation chunks
    chunks_resp = supabase.table("transcript_chunks") \
        .select("meeting_id, filename, content, timestamp_start") \
        .ilike("content", f"%{question}%") \
        .execute()

    context = []
    citations = []

    # Add structured decisions first
    extracted_rows = (extracted_resp.data or [])[:top_k]
    chunk_rows = (chunks_resp.data or [])[:top_k]

    for row in extracted_rows:
        d = row["data"]
        context.append(f"[{row['meeting_id']}] {d['type'].upper()}: {d['content']}")
        citations.append(f"• {row['meeting_id']} ({row['filename']})")

    # Add surrounding conversation for "why" reasoning
    for row in chunk_rows:
        context.append(f"Conversation from {row['meeting_id']} at {row['timestamp_start']}:\n{row['content']}")
        citations.append(f"• {row['meeting_id']} – {row['filename']} – {row['timestamp_start']}")

    system_prompt = f"""
    You are the Meeting Intelligence Hub assistant.
    Use the context below to answer. Pay special attention to the conversation chunks when the user asks "why" or "what led to".
    Always cite the meeting and timestamp.
    """

    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n" + "\n\n".join(context)}
        ]
    )
    try:
        answer = response["message"]["content"]
    except KeyError:
         answer = "Sorry, I couldn't generate an answer at this time."
    return answer
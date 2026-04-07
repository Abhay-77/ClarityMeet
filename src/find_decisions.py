import json
import os
from dotenv import load_dotenv
from src.cloudflare_ai import chat

load_dotenv()
CF_CHAT_MODEL = os.getenv("CF_CHAT_MODEL", "@cf/meta/llama-3-8b-instruct")

def find_decisions(transcript_entries):
    # Convert entries to clean full transcript text
    full_text = "\n".join(
        f"{entry['timestamp']} | {entry['speaker']} | {entry['content']}"
        for entry in transcript_entries
    )

    SYSTEM_PROMPT = """
    You are an expert meeting analyst for the Meeting Intelligence Hub.

    Analyze the ENTIRE transcript and return ONLY real decisions and action items.

    CRITICAL RULES:
    - Agenda items ("John will present...", "Today we will discuss...") → ignore
    - Only mark a DECISION when the team clearly agrees ("decision made", "agreed", "yes" after proposal)
    - Only mark an ACTION ITEM when there is a clear owner + task + deadline
    - When someone assigns a task but another person accepts ("Yes, I'll do it"), the owner is the person who accepted
    - ALWAYS include the deadline in the "action_item" text like: "Fix token refresh issue by April 10th"
    - Capture EVERY decision, including the 3-day buffer
    - Treat each distinct agreement as a separate decision. Do not merge the main delay decision with the later 3-day buffer decision.

    Return ONLY a JSON array of objects with this exact schema:
    [
    {
        "timestamp": "HH:MM",
        "speaker": "speaker name",
        "type": "decision" or "action_item",
        "decision": "short summary of decision (empty if action_item)",
        "action_item": "task summary INCLUDING deadline (empty if decision)",
        "who": "responsible person (only for action_item)",
        "when": "deadline like 2025-04-10 or ASAP (only for action_item)"
    }
    ]
    If nothing found, return an empty array [].
    """

    response_text = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_text}
        ],
        CF_CHAT_MODEL,
    )

    try:
        items = json.loads(response_text)
    except (json.JSONDecodeError, KeyError):
        items = []

    return items
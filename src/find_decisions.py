import ollama
import json

prompt = (
    "You analyze a single meeting transcript entry and return structured JSON. "
    "Only mark a decision if a concrete choice has been made (e.g., a selected option). "
    "If the entry presents options without a final choice, it is not a decision. "
    "Only mark an action_item if there is a specific task to be done. "
    "If neither applies, use type 'none'. "
    "Return JSON with: type, decision, action_item. "
    "For type 'decision', decision is a short summary of the decision made. "
    "For type 'action_item', action_item is the task summary. "
    "For type 'none', both decision and action_item are empty strings."
)

def find_decisions(transcript_entries):
    decisions = []
    for i in range(len(transcript_entries)):
        entry = transcript_entries[i]
        content = entry['content']

        response = ollama.chat(
            model="qwen3:8b",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": content}],
            format={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["decision", "action_item", "none"]},
                    "decision": {"type": "string"},
                    "action_item": {"type": "string"}
                },
                "required": ["type", "decision", "action_item"],
                "additionalProperties": False
            }
        )
        data = json.loads(response.message.content)

        transcript_entries[i]['type'] = data['type']
        transcript_entries[i]['decision'] = data['decision']
        transcript_entries[i]['action_item'] = data['action_item']
    return transcript_entries


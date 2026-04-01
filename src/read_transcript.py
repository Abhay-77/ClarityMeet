from pathlib import Path
import json
import re

def read_transcript(file_path):
    try:
        transcript_text = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print("The specified file was not found. Please check the path and try again.")
    else:
        entry_pattern = re.compile(r"^\[(\d{2}:\d{2})\]\s*(.+?):\s*(.+)$")
        transcript_entries = []

        for raw_line in transcript_text.splitlines():
            line = raw_line.strip()

            if not line or set(line) == {'-'}:
                continue

            match = entry_pattern.match(line)
            if match:
                timestamp, speaker, content = match.groups()
                transcript_entries.append({
                    "timestamp": timestamp,
                    "speaker": speaker.strip(),
                    "content": content.strip()
                })
            elif transcript_entries:
                transcript_entries[-1]["content"] += " " + line

        return transcript_entries
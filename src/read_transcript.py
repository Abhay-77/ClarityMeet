from pathlib import Path
import re

TXT_SPEAKER_PATTERN = re.compile(r"^\[(\d{2}:\d{2})\]\s*(.+?):\s*(.+)$")
TXT_NO_SPEAKER_PATTERN = re.compile(r"^\[(\d{2}:\d{2})\]\s*(.+)$")
VTT_CUE_PATTERN = re.compile(
    r"^(\d{2}:)?\d{2}:\d{2}\.\d{3}\s*-->\s*(\d{2}:)?\d{2}:\d{2}\.\d{3}"
)
VTT_TIMESTAMP_PATTERN = re.compile(r"^(\d{2}:)?\d{2}:\d{2}\.\d{3}")
VTT_SPEAKER_PATTERN = re.compile(r"^([A-Za-z][^:]{0,40}):\s*(.+)$")


def normalize_vtt_timestamp(raw_timestamp):
    time_only = raw_timestamp.split(" ")[0]
    parts = time_only.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        hours = "0"
        minutes, seconds = parts
    seconds = seconds.split(".")[0]
    total_minutes = int(hours) * 60 + int(minutes)
    return f"{total_minutes:02d}:{int(seconds):02d}"


def create_entry(timestamp, speaker, content):
    normalized_speaker = speaker.strip() if speaker else "NONE"
    return {
        "timestamp": timestamp,
        "speaker": normalized_speaker,
        "content": content.strip(),
    }


def parse_txt_transcript(transcript_text):
    transcript_entries = []

    for raw_line in transcript_text.splitlines():
        line = raw_line.strip()

        if not line or set(line) == {"-"}:
            continue

        match = TXT_SPEAKER_PATTERN.match(line)
        if match:
            timestamp, speaker, content = match.groups()
            transcript_entries.append(create_entry(timestamp, speaker, content))
            continue

        match = TXT_NO_SPEAKER_PATTERN.match(line)
        if match:
            timestamp, content = match.groups()
            transcript_entries.append(create_entry(timestamp, "NONE", content))
            continue

        if transcript_entries:
            transcript_entries[-1]["content"] += " " + line
        else:
            transcript_entries.append(create_entry("", "NONE", line))

    return transcript_entries


def parse_vtt_transcript(transcript_text):
    transcript_entries = []
    current_timestamp = ""
    buffer = []

    def flush_buffer():
        nonlocal buffer, current_timestamp
        if not current_timestamp or not buffer:
            buffer = []
            return

        text = " ".join(buffer).strip()
        if not text:
            buffer = []
            return

        speaker = "NONE"
        content = text
        speaker_match = VTT_SPEAKER_PATTERN.match(buffer[0])
        if speaker_match:
            speaker, first_line = speaker_match.groups()
            remaining = [first_line] + buffer[1:]
            content = " ".join(remaining).strip()

        transcript_entries.append(create_entry(current_timestamp, speaker, content))
        buffer = []

    for raw_line in transcript_text.splitlines():
        line = raw_line.strip()

        if not line:
            flush_buffer()
            current_timestamp = ""
            continue

        if line.upper() == "WEBVTT":
            continue

        if line.isdigit():
            continue

        if VTT_CUE_PATTERN.match(line):
            timestamp_match = VTT_TIMESTAMP_PATTERN.match(line)
            if timestamp_match:
                current_timestamp = normalize_vtt_timestamp(timestamp_match.group(0))
            else:
                current_timestamp = ""
            buffer = []
            continue

        if current_timestamp:
            buffer.append(line)

    flush_buffer()
    return transcript_entries


def read_transcript_text(transcript_text, suffix):
    if suffix == ".vtt":
        return parse_vtt_transcript(transcript_text)
    return parse_txt_transcript(transcript_text)


def read_transcript(file_path):
    try:
        transcript_text = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print("The specified file was not found. Please check the path and try again.")
        return []

    suffix = Path(file_path).suffix.lower()
    return read_transcript_text(transcript_text, suffix)
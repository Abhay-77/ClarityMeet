from fastapi import FastAPI, File, HTTPException, UploadFile

from .find_decisions import find_decisions
from .read_transcript import read_transcript_text

app = FastAPI(title="ClarityMeet API")


@app.post("/api/parse")
async def parse_transcript(file: UploadFile = File(...)):
    suffix = (file.filename or "").lower()
    if not (suffix.endswith(".vtt") or suffix.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only .vtt or .txt files are supported.")
    print(f"Received file: {file.filename}")

    try:
        raw_bytes = await file.read()
        transcript_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.") from exc

    entries = read_transcript_text(transcript_text, ".vtt" if suffix.endswith(".vtt") else ".txt")
    parsed_entries = find_decisions(entries)
    return {"entries": parsed_entries}
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4

from .find_decisions import find_decisions
from .read_transcript import read_transcript_text
from .minutes import generate_meeting_minutes
from .store_search_db import ask_meeting_intelligence, save_transcript_and_extracted

app = FastAPI(title="ClarityMeet API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clarity-meet-five.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class MinutesRequest(BaseModel):
    meeting_id: str


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

    meeting_id = uuid4().hex
    save_transcript_and_extracted(
        meeting_id=meeting_id,
        filename=file.filename or "transcript",
        transcript_entries=entries,
        extracted_list=parsed_entries,
        original_file_bytes=raw_bytes,
    )

    return {"meeting_id": meeting_id, "entries": parsed_entries}


@app.post("/api/ask")
async def ask_intelligence(payload: AskRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    answer = ask_meeting_intelligence(payload.question.strip())
    return {"answer": answer}


@app.post("/api/minutes")
async def generate_minutes(payload: MinutesRequest):
    if not payload.meeting_id.strip():
        raise HTTPException(status_code=400, detail="Meeting ID cannot be empty.")

    minutes = generate_meeting_minutes(payload.meeting_id.strip())
    return {"minutes": minutes}


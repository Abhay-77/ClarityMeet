# ClarityMeet

## Project Title

ClarityMeet - Meeting intelligence with transcript parsing, decisions, and minutes.

## The Problem

Teams lose track of decisions and action items buried in long meeting transcripts. Manually summarizing meetings is slow and inconsistent, and it is hard to answer follow-up questions about why a decision was made.

## The Solution

ClarityMeet parses uploaded transcripts, extracts decisions and action items, stores structured data and semantic embeddings, and provides a chat-style meeting intelligence endpoint. It can also generate concise meeting minutes from the stored context to make follow-up and accountability easy.

## Tech Stack

- Languages: Python, JavaScript
- Backend: FastAPI
- Frontend: React (Vite)
- Database: Supabase (PostgreSQL + pgvector)
- Storage: Supabase Storage (optional)
- AI models: Cloudflare Workers AI (@cf/meta/llama-3-8b-instruct, @cf/baai/bge-large-en-v1.5)

## Database Schema

### extracted_items

- id (int8)
- meeting_id (text)
- filename (text)
- meeting_date (date)
- item_type (text)
- data (jsonb)
- created_at (timestamptz)

### transcript_chunks

- id (int8)
- meeting_id (text)
- filename (text)
- chunk_index (int4)
- content (text)
- timestamp_start (text)
- timestamp_end (text)
- created_at (timestamptz)
- embedding (vector)

## Setup Instructions

### Backend

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the repo root with:
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
4. Set Cloudflare Workers AI model IDs (optional overrides):
   ```bash
   CF_CHAT_MODEL=@cf/meta/llama-3-8b-instruct
   CF_EMBED_MODEL=@cf/baai/bge-large-en-v1.5
   ```
5. Start the API:
   ```bash
   uvicorn src.main:app --reload
   ```

### Frontend

Hosted frontend: https://clarity-meet-five.vercel.app/

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev
   ```

### Supabase Notes

- Create tables `extracted_items` and `transcript_chunks`.
- Enable `pgvector` and add an `embedding` column to `transcript_chunks`.
- Create an RPC function `match_chunks` for vector similarity search.
- Create a Storage bucket named `transcripts` if you want to store raw uploads.

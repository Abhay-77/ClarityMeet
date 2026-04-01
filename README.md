# ClarityMeet

ClarityMeet is a small Python prototype that reads a meeting transcript and uses an LLM to label each entry as a decision, an action item, or none. It currently targets a local Ollama model and prints structured results to stdout.

## Current Status

- **Working prototype**: Parses transcript lines into timestamp/speaker/content entries.
- **LLM classification**: Sends each entry to Ollama (`qwen3:8b`) and expects strict JSON output.
- **Console output**: Prints only entries that are not `none` with decision/action item fields.
- **Test sample**: Includes a sample transcript in `tests/prod_start_meet.txt`.

## How It Works

1. `read_transcript.py` reads a transcript file and builds a list of entries.
2. `find_decisions.py` calls Ollama for each entry to classify it.
3. `main.py` wires the steps together and prints the results.

## Run

```bash
python src/main.py
```

By default, `main.py` reads:

- `./tests/prod_start_meet.txt`

## Requirements

- Python 3.x
- Ollama running locally with the `qwen3:8b` model available
- Install dependencies: `pip install -r requirements.txt`

## Known Limitations

- `main.py` uses a hardcoded transcript path (no CLI args yet).
- No batching, caching, or retries for Ollama calls.
- No test runner or automated tests yet.

## Next Ideas

- Add CLI arguments for transcript path and output format.
- Add basic tests.
- Persist results to JSON/CSV instead of only printing.
- Improve prompt and include context across multiple entries.

# Ciryx Vibe — Project Instructions

## What This Is

Sentiment analysis REST API. Single Python file (`app.py`) served via gunicorn in Docker.
Uses HuggingFace `cardiffnlp/twitter-roberta-base-sentiment-latest` model.

## Project Structure

```
app.py              — Flask app + CiryxVibe analysis class (all logic lives here)
Dockerfile          — Python 3.11-slim, non-root user, gunicorn entrypoint
docker-compose.yml  — Service definition, health checks, volume mounts
requirements.txt    — Pinned dependencies
models/             — HuggingFace model cache (gitignored, populated at runtime)
logs/               — Application logs (gitignored)
```

## Key Architecture Decisions

- **Single file**: All routes and the ML class are in `app.py`. Don't split unless it grows past ~300 lines.
- **Gunicorn with 1 worker**: The model is large (~500MB in memory). Multiple workers would duplicate it. Scale horizontally with containers instead.
- **Model loads at startup**: `CiryxVibe()` is instantiated at module level. First request will be fast, but container startup takes 60-120s.

## How to Run

```bash
docker compose up --build        # Full container
python app.py                    # Local dev (needs deps installed)
```

## API Endpoints

- `GET /`         — API overview
- `GET /health`   — Health check (used by Docker healthcheck)
- `POST /analyze` — Single text analysis (`{"text": "..."}`)
- `POST /batch`   — Batch analysis (`{"texts": ["...", "..."]}`)

## Development Rules

- No secrets in code. Use environment variables.
- Keep `app.py` self-contained. Avoid unnecessary abstractions.
- Test with: `curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d '{"text": "test"}'`
- Commit after meaningful changes, not every edit.

# Ciryx Vibe

**AI-powered sentiment analysis API** built on HuggingFace's RoBERTa model. Accepts text, returns positive / neutral / negative sentiment with confidence scores.

Packaged as a Docker container for one-command deployment.

## Quick Start

```bash
# Clone and run
git clone https://github.com/cryptoken/Ciryx-Vibe.git
cd Ciryx-Vibe
docker compose up --build
```

The API is live at `http://localhost:5000` once the model finishes loading (~60-120s on first run).

## API Reference

### `GET /` — Overview

Returns available endpoints and usage hints.

### `GET /health` — Health Check

```json
{ "status": "healthy", "service": "Ciryx Vibe", "version": "1.0.0" }
```

### `POST /analyze` — Single Text

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "input_text": "I love this product!",
    "sentiment": "positive",
    "confidence": 0.9734,
    "processing_time_ms": 42.31
  }
}
```

### `POST /batch` — Multiple Texts (up to 100)

```bash
curl -X POST http://localhost:5000/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great service!", "Terrible experience.", "It was okay."]}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      { "index": 0, "sentiment": "positive", "confidence": 0.9621 },
      { "index": 1, "sentiment": "negative", "confidence": 0.9512 },
      { "index": 2, "sentiment": "neutral",  "confidence": 0.7843 }
    ],
    "summary": {
      "total_texts": 3,
      "successful": 3,
      "total_processing_time_ms": 127.45
    }
  }
}
```

## Architecture

```
Client  →  Flask API (gunicorn)  →  CiryxVibe class  →  HuggingFace pipeline
                                                            ↓
                                              cardiffnlp/twitter-roberta-base-sentiment-latest
```

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask application with all routes and the `CiryxVibe` analysis class |
| `Dockerfile` | Container image with Python 3.11, non-root user, health checks |
| `docker-compose.yml` | Service orchestration with volume mounts and networking |
| `requirements.txt` | Pinned Python dependencies |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Flask environment mode |
| `PYTHONUNBUFFERED` | `1` | Immediate log output |

## Limits

- Single text: max **5,000 characters**
- Batch: max **100 texts** per request
- Model: optimized for short-form English text (tweets, reviews, comments)

## Development

```bash
# Run locally (requires Python 3.11+ and ~2GB for model download)
pip install -r requirements.txt
python app.py
```

## License

MIT

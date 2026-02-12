# Ciryx Vibe — Product Requirements Document

## Overview

Ciryx Vibe is a containerized sentiment analysis API that classifies English text as **positive**, **neutral**, or **negative** with a confidence score. It targets developers and businesses that need to integrate sentiment analysis into their applications without managing ML infrastructure.

## Problem

Teams building customer-facing products (support tools, social listening dashboards, review aggregators) need sentiment analysis but don't want to:

1. Train and host their own ML models
2. Pay per-call pricing to third-party NLP APIs at scale
3. Send sensitive customer text to external services

Ciryx Vibe runs on their infrastructure, processes text locally, and charges nothing per call.

## Target Users

- **Backend developers** integrating sentiment into existing apps via REST API
- **Data teams** running batch analysis on customer feedback, reviews, or survey responses
- **DevOps engineers** deploying the service via Docker on any infrastructure

## Core Features

### v1.0 (Current)

| Feature | Description | Status |
|---------|-------------|--------|
| Single text analysis | `POST /analyze` with one text string | Done |
| Batch analysis | `POST /batch` with up to 100 texts | Done |
| Health check | `GET /health` for monitoring and orchestration | Done |
| Docker packaging | One-command deploy via `docker compose up` | Done |
| GPU support | Automatic CUDA detection and GPU offload | Done |
| Confidence scores | 0-1 confidence value per prediction | Done |
| Processing time | Per-request latency tracking in response | Done |

### v1.1 (Planned)

| Feature | Description | Priority |
|---------|-------------|----------|
| API key auth | Bearer token authentication for production use | High |
| Rate limiting | Per-key request throttling | High |
| Multi-language | Support for non-English text via multilingual models | Medium |
| Webhook callbacks | Async batch processing with result delivery | Medium |
| Prometheus metrics | `/metrics` endpoint for observability | Low |

### v2.0 (Future)

| Feature | Description |
|---------|-------------|
| Custom model support | Bring-your-own fine-tuned model |
| Aspect-based sentiment | Per-topic sentiment within a single text |
| Emotion detection | Beyond pos/neg/neutral — anger, joy, sadness, etc. |
| Streaming analysis | WebSocket endpoint for real-time text streams |

## Technical Constraints

- **Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest` — optimized for short-form English text
- **Memory**: ~500MB for model in memory; single gunicorn worker to avoid duplication
- **Startup**: 60-120s cold start (model download + load)
- **Input limits**: 5,000 chars per text, 100 texts per batch
- **No persistence**: Stateless API; no database, no stored results

## Success Metrics

| Metric | Target |
|--------|--------|
| Single text latency (CPU) | < 200ms p95 |
| Batch throughput (CPU) | 100 texts in < 10s |
| Container startup | < 120s (cached model) |
| Uptime | 99.9% with Docker restart policy |
| Accuracy | Matches published model benchmarks (~94% on TweetEval) |

## Non-Goals

- Not a UI product — API only
- Not a model training platform
- Not a multi-tenant SaaS (single-instance deployment)
- Not real-time streaming (v1.0 is request/response only)

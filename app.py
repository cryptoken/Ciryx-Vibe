from flask import Flask, request, jsonify
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class CiryxVibe:
    """Sentiment analysis engine using HuggingFace's RoBERTa model."""

    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    SENTIMENT_MAP = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
        "NEGATIVE": "negative",
        "NEUTRAL": "neutral",
        "POSITIVE": "positive",
    }

    def __init__(self):
        self.model_name = self.MODEL_NAME
        self._load_model()

    def _load_model(self):
        logger.info("Loading sentiment model: %s", self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1,
        )
        logger.info("Model loaded successfully")

    def analyze(self, text: str) -> dict:
        start = time.time()
        result = self.sentiment_pipeline(text)[0]
        sentiment = self.SENTIMENT_MAP.get(result["label"].upper(), result["label"].lower())
        return {
            "sentiment": sentiment,
            "confidence": round(result["score"], 4),
            "processing_time_ms": round((time.time() - start) * 1000, 2),
        }


vibe = CiryxVibe()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Routes ---


@app.route("/", methods=["GET"])
def root():
    """API overview and usage hints."""
    return jsonify({
        "service": "Ciryx Vibe Sentiment Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "GET  /":        "This overview",
            "GET  /health":  "Health check",
            "POST /analyze": "Analyze a single text",
            "POST /batch":   "Analyze up to 100 texts",
        },
        "example": {
            "url": "/analyze",
            "method": "POST",
            "body": {"text": "I love this product!"},
        },
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Ciryx Vibe",
        "version": "1.0.0",
        "timestamp": _utcnow(),
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze sentiment of a single text."""
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text", "code": "MISSING_TEXT"}), 400

    text = data["text"]
    if not text.strip():
        return jsonify({"error": "Text cannot be empty", "code": "EMPTY_TEXT"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text too long (max 5000 chars)", "code": "TEXT_TOO_LONG"}), 400

    try:
        result = vibe.analyze(text)
    except Exception:
        logger.exception("Analysis failed")
        return jsonify({"error": "Internal server error", "code": "ANALYSIS_ERROR"}), 500

    return jsonify({
        "success": True,
        "data": {
            "input_text": (text[:100] + "...") if len(text) > 100 else text,
            **result,
        },
        "metadata": {
            "model": vibe.model_name,
            "service": "Ciryx Vibe",
            "timestamp": _utcnow(),
        },
    })


@app.route("/batch", methods=["POST"])
def batch():
    """Analyze up to 100 texts in a single request."""
    data = request.get_json(silent=True)
    if not data or "texts" not in data:
        return jsonify({"error": "Missing required field: texts (array)", "code": "MISSING_TEXTS"}), 400

    texts = data["texts"]
    if not isinstance(texts, list):
        return jsonify({"error": "texts must be an array", "code": "INVALID_FORMAT"}), 400
    if len(texts) > 100:
        return jsonify({"error": "Maximum 100 texts per batch", "code": "BATCH_TOO_LARGE"}), 400

    results = []
    total_start = time.time()

    for i, text in enumerate(texts):
        if not text or not text.strip():
            results.append({"index": i, "error": "Empty text", "sentiment": None, "confidence": None})
            continue
        try:
            r = vibe.analyze(text)
            results.append({
                "index": i,
                "text_preview": (text[:50] + "...") if len(text) > 50 else text,
                **r,
            })
        except Exception as e:
            results.append({"index": i, "error": str(e), "sentiment": None, "confidence": None})

    return jsonify({
        "success": True,
        "data": {
            "results": results,
            "summary": {
                "total_texts": len(texts),
                "successful": sum(1 for r in results if r.get("sentiment")),
                "total_processing_time_ms": round((time.time() - total_start) * 1000, 2),
            },
        },
        "metadata": {
            "model": vibe.model_name,
            "service": "Ciryx Vibe",
            "timestamp": _utcnow(),
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
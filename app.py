# IMPORTS - All the libraries we need
from flask import Flask, request, jsonify
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
from datetime import datetime

# LOGGING SETUP - So we can debug issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FLASK APP CREATION
app = Flask(__name__)

# MAIN AI CLASS - This handles all the sentiment analysis
class CiryxVibe:
    def __init__(self):
        # Which AI model to use (this one is good for social media/general text)
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.load_model()
        
    def load_model(self):
        """Download and load the AI model - this happens once at startup"""
        try:
            logger.info("Loading Ciryx Vibe sentiment model...")
            
            # Download tokenizer (converts text to numbers for AI)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Download the actual AI model (this is the big download)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create a pipeline for easy use (combines tokenizer + model)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            
            logger.info("Ciryx Vibe model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def analyze_sentiment(self, text):
        """The core function - analyze sentiment of any text"""
        try:
            start_time = time.time()
            
            # Run the AI model on the text
            result = self.sentiment_pipeline(text)[0]
            
            # Extract results
            label = result['label']
            confidence = result['score']
            
            # Convert AI labels to business-friendly terms
            sentiment_mapping = {
                'LABEL_0': 'negative',    # AI model uses numbers
                'LABEL_1': 'neutral', 
                'LABEL_2': 'positive',
                'NEGATIVE': 'negative',   # Some models use words
                'NEUTRAL': 'neutral',
                'POSITIVE': 'positive'
            }
            
            sentiment = sentiment_mapping.get(label.upper(), label.lower())
            
            # Calculate how long it took
            processing_time = time.time() - start_time
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 4),
                'processing_time_ms': round(processing_time * 1000, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise

# CREATE THE AI ANALYZER (this loads the model when container starts)
vibe_analyzer = CiryxVibe()

# API ENDPOINTS - These are the URLs businesses will call

@app.route('/health', methods=['GET'])
def health_check():
    """Health check - tells Docker/monitoring systems we're working"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ciryx Vibe',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    """Main endpoint - analyze single piece of text"""
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        # VALIDATION - make sure we have text to analyze
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text',
                'code': 'MISSING_TEXT'
            }), 400
            
        text = data['text']
        
        # More validation
        if not text.strip():
            return jsonify({
                'error': 'Text cannot be empty',
                'code': 'EMPTY_TEXT'
            }), 400
            
        if len(text) > 5000:
            return jsonify({
                'error': 'Text too long. Maximum 5000 characters.',
                'code': 'TEXT_TOO_LONG'
            }), 400
        
        # RUN THE AI ANALYSIS
        result = vibe_analyzer.analyze_sentiment(text)
        
        # RETURN BUSINESS-FRIENDLY RESPONSE
        return jsonify({
            'success': True,
            'data': {
                'input_text': text[:100] + "..." if len(text) > 100 else text,
                'sentiment': result['sentiment'],
                'confidence': result['confidence'],
                'processing_time_ms': result['processing_time_ms']
            },
            'metadata': {
                'model': vibe_analyzer.model_name,
                'service': 'Ciryx Vibe',
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'ANALYSIS_ERROR'
        }), 500

@app.route('/batch', methods=['POST'])
def batch_analyze():
    """Batch endpoint - analyze multiple texts at once (for businesses with lots of data)"""
    try:
        data = request.get_json()
        
        if not data or 'texts' not in data:
            return jsonify({
                'error': 'Missing required field: texts (array)',
                'code': 'MISSING_TEXTS'
            }), 400
            
        texts = data['texts']
        
        if not isinstance(texts, list):
            return jsonify({
                'error': 'texts must be an array',
                'code': 'INVALID_FORMAT'
            }), 400
            
        if len(texts) > 100:
            return jsonify({
                'error': 'Maximum 100 texts per batch',
                'code': 'BATCH_TOO_LARGE'
            }), 400
        
        # PROCESS EACH TEXT
        results = []
        total_start_time = time.time()
        
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append({
                    'index': i,
                    'error': 'Empty text',
                    'sentiment': None,
                    'confidence': None
                })
                continue
                
            try:
                result = vibe_analyzer.analyze_sentiment(text)
                results.append({
                    'index': i,
                    'text_preview': text[:50] + "..." if len(text) > 50 else text,
                    'sentiment': result['sentiment'],
                    'confidence': result['confidence'],
                    'processing_time_ms': result['processing_time_ms']
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'error': str(e),
                    'sentiment': None,
                    'confidence': None
                })
        
        total_processing_time = time.time() - total_start_time
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'summary': {
                    'total_texts': len(texts),
                    'successful_analyses': len([r for r in results if 'sentiment' in r and r['sentiment']]),
                    'total_processing_time_ms': round(total_processing_time * 1000, 2)
                }
            },
            'metadata': {
                'model': vibe_analyzer.model_name,
                'service': 'Ciryx Vibe',
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'BATCH_ERROR'
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - shows API documentation"""
    return jsonify({
        'service': 'Ciryx Vibe Sentiment Analysis API',
        'version': '1.0.0',
        'description': 'AI-powered sentiment analysis for business applications',
        'endpoints': {
            'health': 'GET /health',
            'analyze': 'POST /analyze',
            'batch': 'POST /batch'
        },
        'example': {
            'analyze': {
                'url': '/analyze',
                'method': 'POST',
                'body': {'text': 'I love this product!'}
            }
        }
    })

# START THE SERVER - this runs when container starts
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
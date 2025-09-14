# Simple single-stage build (easier to debug)
FROM python:3.9-slim

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash ciryx

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies as root (simpler)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create directories for models and logs
RUN mkdir -p /app/models /app/logs

# Give ownership to our non-root user
RUN chown -R ciryx:ciryx /app

# Switch to non-root user
USER ciryx

# Flask configuration
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Metadata
LABEL maintainer="Ciryx AI"
LABEL version="1.0.0"
LABEL description="Ciryx Vibe - Enterprise Sentiment Analysis API"

# Start the application
CMD ["python", "app.py"]
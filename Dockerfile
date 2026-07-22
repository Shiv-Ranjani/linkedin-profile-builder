# ---------------------------------------------------------------------------
# Production Dockerfile for the AI LinkedIn Profile Builder
# Base: Python 3.11 slim  |  Runs Streamlit on port 8080 (Cloud Run default)
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Streamlit / Python runtime configuration.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies first so this layer is cached until requirements change.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application source (respecting .dockerignore).
COPY . .

# Run as a non-root user for better security.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Cloud Run sets $PORT; default to 8080 for local runs.
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]

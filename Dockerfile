# ── Cinematic Decoder — Dockerfile ────────────────────────────────────────────
# Compatible with arm64 (Apple Silicon / OrbStack) and amd64.
# Uses the official python:3.12-slim image which ships multi-arch manifests.

FROM python:3.12-slim

# Metadata
LABEL maintainer="Cinematic Decoder" \
      description="AI Movie Companion — Streamlit App" \
      version="1.0.0"

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Streamlit config — disable telemetry and set server options
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml

# Switch to non-root user
USER appuser

# Expose Streamlit's default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Run the app
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0"]

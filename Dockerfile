# Production-ready Dockerfile for OCR API
# Multi-stage build for optimal size and security

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code (explicit copy for control)
COPY main.py .
COPY config.py .
COPY models.py .
COPY services/ ./services/
COPY utils/ ./utils/
COPY middleware/ ./middleware/
COPY static/ ./static/

# Set PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Environment variables
ENV PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Cloud Run required port
EXPOSE 8080

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

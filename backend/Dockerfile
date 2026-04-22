FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py || exit 1

EXPOSE 8000

# Default to production settings
# Override with --reload for development: docker run -e DEBUG=true -e ENV=development
CMD ["sh", "-c", "\
    # Run Alembic migrations\
    alembic upgrade head && \
    # Start uvicorn\
    uvicorn main:app --host 0.0.0.0 --port 8000 \
"]

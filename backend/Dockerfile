# Production Dockerfile for Field Service Dispatch Backend
FROM python:3.10-slim

WORKDIR /app

# Install system build tools and postgresql client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application directory to /app/backend
COPY backend /app/backend

# Set Python path to include /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000

# Run backend production server with dynamic PORT expansion
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

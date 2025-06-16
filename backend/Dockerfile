# Multi-stage build for optimized uv usage
FROM python:3.12-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-cache

# Production stage
FROM python:3.12-slim

# Install system dependencies (like ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app_backend

# Copy the virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Make sure we use the venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application (will be overridden by docker-compose for development)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

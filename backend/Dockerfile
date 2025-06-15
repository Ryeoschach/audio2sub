FROM python:3.9-slim

# Set working directory
WORKDIR /app_backend

# Install system dependencies (like ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements file and install Python dependencies using uv
COPY requirements.txt requirements.txt
# Using --system as we are in a Docker container, not creating a sub-venv
RUN uv pip install --no-cache -r requirements.txt --system

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application (will be overridden by docker-compose for development)
# For production, you might use: uvicorn app.main:app --host 0.0.0.0 --port 8000
# For Celery worker, this Dockerfile can also be used, but the command will be different.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# LMS Backend Python Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure uploads directories exist
RUN mkdir -p uploads/videos uploads/documents uploads/profiles temp

EXPOSE 3000

# Start ASGI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]

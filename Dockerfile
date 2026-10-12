# Simple Dockerfile with Gunicorn
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories (no database folder needed)
RUN mkdir -p logs static/data

# Set proper permissions
RUN chmod 755 static/data

# Expose port (Render injects $PORT, locally it defaults to 5000)
ENV PORT=5000
EXPOSE 5000

# Run with Gunicorn. A single worker because the conversation state lives in memory;
# threads handle concurrent requests and the long timeout covers slow OpenAI responses
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app


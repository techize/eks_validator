# EKS Cluster Validator Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash validator
RUN chown -R validator:validator /app
USER validator

# Create directories for logs and reports
RUN mkdir -p logs reports

# Set entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command
CMD ["--help"]

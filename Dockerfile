# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements_versions.txt requirements-commercial.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_versions.txt
RUN pip install --no-cache-dir -r requirements-commercial.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models/checkpoints models/loras outputs temp logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash capsule
RUN chown -R capsule:capsule /app
USER capsule

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start the application
CMD ["python", "entry_with_update.py", "--listen", "--port", "7860"]
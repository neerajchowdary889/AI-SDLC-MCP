FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY cloud_requirements.txt .
RUN pip install --no-cache-dir -r cloud_requirements.txt

# Copy application code
COPY src/ ./src/
COPY cloud_server.py .
COPY docs/ ./docs/

# Create necessary directories
RUN mkdir -p ./docs ./index

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV MCP_API_KEY=your-secret-api-key-here

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "cloud_server.py"]
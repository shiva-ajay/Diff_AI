# Use Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies required for OpenCV and other packages
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgl1-mesa-dev \
    libglib2.0-dev \
    libgthread-2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies only (no local package)
RUN poetry install --only=main --no-interaction --no-ansi --no-root

# Copy project files
COPY . .

# Install the local package
RUN poetry install --only-root --no-interaction --no-ansi

# Create necessary directories
RUN mkdir -p results static
RUN chmod 755 results static

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONUNBUFFERED=1", "PYTHONPATH=/app", "python", "app.py"]



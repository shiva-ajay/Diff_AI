# Use Python 3.10 as base image (slim version for smaller image size)
FROM python:3.10-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install poetry with compatible versions of dependencies
RUN pip install --no-cache-dir "setuptools<68.0.0" && \
    pip install --no-cache-dir "poetry==1.4.2"

# Copy the entire project code
COPY . .

# Configure poetry to not create a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install project dependencies
RUN poetry install --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]